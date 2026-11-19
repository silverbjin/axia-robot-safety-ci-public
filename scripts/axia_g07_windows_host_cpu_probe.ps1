# AXIA CV2 HFbm WSL2 CPU hypothesis: independent Windows host sampler.
# No ROS/Gazebo control; no process priority, power plan, CPU affinity change.
# Run from the public WSL2 diagnostic wrapper, never directly for Goal consent.
param(
  [Parameter(Mandatory=$true)][string]$OutputPath,
  [Parameter(Mandatory=$true)][string]$StopPath,
  [int]$IntervalMs=150
)
$ErrorActionPreference='Stop'
if ($IntervalMs -lt 100 -or $IntervalMs -gt 500) {
  throw "HOST_PROBE_INTERVAL_OUT_OF_RANGE"
}
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class AxiaCpuTimes {
  [StructLayout(LayoutKind.Sequential)]
  public struct FT {
    public uint Low;
    public uint High;
    public long AsLong() { return ((long)High << 32) | (long)Low; }
  }
  [DllImport("kernel32.dll", SetLastError=true)]
  public static extern bool GetSystemTimes(out FT idle,out FT kernel,out FT user);
}
'@
$parent=[System.IO.Path]::GetDirectoryName($OutputPath)
[System.IO.Directory]::CreateDirectory($parent) | Out-Null
$writer=[System.IO.StreamWriter]::new($OutputPath,$false,[System.Text.UTF8Encoding]::new($false))
$writer.AutoFlush=$true
$sw=[System.Diagnostics.Stopwatch]::StartNew()
$lastElapsed=0.0
$priorIdle=[long]0
$priorTotal=[long]0
$first=$true
$logical=[Environment]::ProcessorCount
try {
  while (-not [System.IO.File]::Exists($StopPath)) {
    $elapsed=$sw.Elapsed.TotalMilliseconds
    $gap=$elapsed-$lastElapsed
    $lastElapsed=$elapsed
    $idle=[AxiaCpuTimes+FT]::new()
    $kernel=[AxiaCpuTimes+FT]::new()
    $user=[AxiaCpuTimes+FT]::new()
    $ok=[AxiaCpuTimes]::GetSystemTimes([ref]$idle,[ref]$kernel,[ref]$user)
    $cpuPct=$null
    if ($ok) {
      $idle64=$idle.AsLong()
      $total64=$kernel.AsLong()+$user.AsLong()
      if (-not $first -and $total64 -gt $priorTotal) {
        $cpuPct=[Math]::Round(100*(1-($idle64-$priorIdle)/[double]($total64-$priorTotal)),2)
      }
      $priorIdle=$idle64
      $priorTotal=$total64
    }
    $first=$false
    $vmmem=@(Get-Process -Name 'VmmemWSL','Vmmem' -ErrorAction SilentlyContinue)
    $vmmemCpuSec=0.0
    foreach($p in $vmmem){ $vmmemCpuSec+=$p.CPU }
    $row=[ordered]@{
      epoch_ms=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
      gap_ms=[Math]::Round($gap,3)
      host_cpu_pct=$cpuPct
      vmmem_cpu_total_sec=[Math]::Round($vmmemCpuSec,4)
      vmmem_processes=$vmmem.Count
      host_logical_cpus=$logical
    }
    $writer.WriteLine(($row | ConvertTo-Json -Compress -Depth 3))
    Start-Sleep -Milliseconds $IntervalMs
  }
} finally {
  $writer.Flush()
  $writer.Dispose()
}
