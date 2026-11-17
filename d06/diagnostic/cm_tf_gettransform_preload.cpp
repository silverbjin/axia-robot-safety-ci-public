// AXIA G07 CM120: DIAGNOSTIC ONLY, never link into safety production.
// Reuses the official nav2_util::getTransform advanced overload unchanged.
// The same exact ABI name is intercepted via LD_PRELOAD and RTLD_NEXT.
// In a dedicated simulation Goal, measure source->base TF-function elapsed
// and per-thread CPU time; NOT an E-Stop or release benchmark.
#include <nav2_util/robot_utils.hpp>
#include <dlfcn.h>
#include <fcntl.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <time.h>
#include <sys/resource.h>
#include <cstdint>
#include <atomic>
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <memory>

using TransformFn = bool (*)(
  const std::string &, const rclcpp::Time &,
  const std::string &, const rclcpp::Time &,
  const std::string &, const tf2::Duration &,
  const std::shared_ptr<tf2_ros::Buffer>, tf2::Transform &);

namespace {
std::atomic<unsigned> samples{0};
std::atomic<int> fd{-2};
constexpr unsigned kMaxTfSamples=15000;
long long clock_ns(clockid_t id) {
  timespec t{};
  if (::clock_gettime(id, &t) != 0) return -1;
  return static_cast<long long>(t.tv_sec) * 1000000000LL + t.tv_nsec;
}
bool owned_cm() {
  char name[64]{};
  int f=::open("/proc/self/comm", O_RDONLY|O_CLOEXEC);
  if(f<0) return false;
  const ssize_t len=::read(f,name,sizeof(name)-1);
  ::close(f);
  if(len<=0) return false;
  name[len]='\0';
  return ::strncmp(name,"collision_monit",15)==0;
}
int active_fd() {
  int current=fd.load(std::memory_order_acquire);
  if(current!=-2) return current;
  int newfd=-1;
  const char* target=std::getenv("AXIA_G07_CM120_TF_DIAG_FILE");
  // Explicit CI+simulation only, and only inside the official CM process.
  if(target && target[0]=='/' && std::getenv("GITHUB_ACTIONS")
     && ::strcmp(std::getenv("GITHUB_ACTIONS"),"true")==0
     && std::getenv("AXIA_P0_SIM_ONLY")
     && ::strcmp(std::getenv("AXIA_P0_SIM_ONLY"),"1")==0
     && owned_cm()) {
    newfd=::open(target,O_CREAT|O_WRONLY|O_APPEND|O_CLOEXEC,0600);
    if(newfd>=0) {
      const char* ready="AXIA_CM120_TF_DIAG_CM_LIBRARY_LOADED\n";
      (void)::write(newfd,ready,std::strlen(ready));
    }
  }
  int expected=-2;
  if(!fd.compare_exchange_strong(expected,newfd)) {
    if(newfd>=0) ::close(newfd);
    return expected;
  }
  return newfd;
}
// This is ONLY a diagnostic. A zero runqueue delta is meaningful only
// when /proc/sys/kernel/sched_schedstats is explicitly enabled. Never
// enable sysctls or change the CI kernel from inside this library.
bool kernel_schedstats_enabled() {
  const int f=::open("/proc/sys/kernel/sched_schedstats",O_RDONLY|O_CLOEXEC);
  if(f<0) return false;
  char val[8]{};
  const ssize_t n=::read(f,val,sizeof(val)-1);
  ::close(f);
  return n>0 && val[0]=='1';
}
struct SchedSample {
  unsigned long long runtime_ns=0,wait_ns=0,slices=0;
};
bool thread_schedstat(SchedSample &s) {
  const int f=::open("/proc/thread-self/schedstat",O_RDONLY|O_CLOEXEC);
  if(f<0) return false;
  char val[128]{};
  const ssize_t n=::read(f,val,sizeof(val)-1);
  ::close(f);
  if(n<=0) return false;
  return ::sscanf(val,"%llu %llu %llu",&s.runtime_ns,
                  &s.wait_ns,&s.slices)==3;
}
TransformFn actual_transform() {
  auto self = static_cast<TransformFn>(&nav2_util::getTransform);
  Dl_info info{};
  if(!::dladdr(reinterpret_cast<void*>(self),&info) || !info.dli_sname) return nullptr;
  void* p=::dlsym(RTLD_NEXT,info.dli_sname);
  if(!p || p==reinterpret_cast<void*>(self)) return nullptr;
  return reinterpret_cast<TransformFn>(p);
}
}  // namespace

extern "C" __attribute__((visibility("default")))
int axia_cm120_original_transform_linkage_selftest() {
  return actual_transform()!=nullptr ? 1:0;
}

namespace nav2_util {
bool getTransform(
  const std::string & source_frame_id, const rclcpp::Time & source_time,
  const std::string & target_frame_id, const rclcpp::Time & target_time,
  const std::string & fixed_frame_id, const tf2::Duration & transform_tolerance,
  const std::shared_ptr<tf2_ros::Buffer> tf_buffer,
  tf2::Transform & result)
{
  // Exact signature of the existing official advanced TF overload; no
  // fallback, no timing/TF parameter changes. Fail closed if binding absent.
  static TransformFn original=actual_transform();
  if(!original) std::abort();
  const int file=active_fd();
  const bool track=file>=0 && samples.fetch_add(1,std::memory_order_relaxed)<kMaxTfSamples;
  long long m0=-1,c0=-1;
  SchedSample sc0{},sc1{};
  rusage u0{},u1{};
  bool sc0_ok=false;
  bool u0_ok=false;
  if(track) {
    sc0_ok=kernel_schedstats_enabled() && thread_schedstat(sc0);
    u0_ok=(::getrusage(RUSAGE_THREAD,&u0)==0);
    m0=clock_ns(CLOCK_MONOTONIC);
    c0=clock_ns(CLOCK_THREAD_CPUTIME_ID);
  }
  // The original official advanced transform is delegated unchanged.
  const bool ok=original(source_frame_id,source_time,target_frame_id,
                          target_time,fixed_frame_id,transform_tolerance,
                          tf_buffer,result);
  if(track) {
    const long long c1=clock_ns(CLOCK_THREAD_CPUTIME_ID);
    const long long m1=clock_ns(CLOCK_MONOTONIC);
    const bool u1_ok=(::getrusage(RUSAGE_THREAD,&u1)==0);
    const bool sc1_ok=sc0_ok && thread_schedstat(sc1);
    const bool sched_valid=(sc1_ok && u0_ok && u1_ok &&
      sc1.runtime_ns>=sc0.runtime_ns &&
      sc1.wait_ns>=sc0.wait_ns && sc1.slices>=sc0.slices &&
      u1.ru_nvcsw>=u0.ru_nvcsw && u1.ru_nivcsw>=u0.ru_nivcsw);
    const auto run_ns=sched_valid?sc1.runtime_ns-sc0.runtime_ns:0ULL;
    const auto delay_ns=sched_valid?sc1.wait_ns-sc0.wait_ns:0ULL;
    const long v=sched_valid?u1.ru_nvcsw-u0.ru_nvcsw:0;
    const long iv=sched_valid?u1.ru_nivcsw-u0.ru_nivcsw:0;
    char line[512];
    const int count=std::snprintf(line,sizeof(line),
      "TF_ADV pid=%ld tid=%ld mono_start_ns=%lld mono_end_ns=%lld thread_cpu_ns=%lld ok=%d schedstat_valid=%d runqueue_ns=%llu sched_cpu_ns=%llu voluntary_cs=%ld involuntary_cs=%ld\n",
      static_cast<long>(::getpid()),static_cast<long>(::syscall(SYS_gettid)),
      m0,m1,c1-c0,ok?1:0,sched_valid?1:0,delay_ns,run_ns,v,iv);
    if(count>0 && count<static_cast<int>(sizeof(line))) {
      (void)::write(file,line,static_cast<size_t>(count));
    }
  }
  return ok;
}
}  // namespace nav2_util
