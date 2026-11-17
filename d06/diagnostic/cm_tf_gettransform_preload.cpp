// AXIA G07 CM120: DIAGNOSTIC ONLY, never link into safety production.
// Reuses the official nav2_util::getTransform advanced overload unchanged.
// The same exact ABI name is intercepted via LD_PRELOAD and RTLD_NEXT.
// In a dedicated simulation Goal, measure source->base TF-function elapsed
// and per-thread CPU time; NOT an E-Stop or release benchmark.
#include <nav2_util/robot_utils.hpp>
#include <rcl/time.h>
#include <rclcpp/clock.hpp>
#include <rcutils/allocator.h>
#include <dlfcn.h>
#include <fcntl.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <time.h>
#include <chrono>
#include <thread>
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
// S2 read-only sleep measurement within the current official Advanced TF
// invocation. The Jazzy tf2 Buffer's 10ms poll uses sleep_for; count only
// genuine intercepted libc sleeps, preserve errno, return and cancellation.
thread_local bool tf_window_active=false;
thread_local long long tf_sleep_wall_ns=0;
thread_local unsigned tf_sleep_calls=0;
thread_local int tf_sleep_depth=0;
std::atomic<unsigned> tf_clock_samples{0};
std::atomic<unsigned> tf_cpp_clock_samples{0};
thread_local bool tf_cpp_clock_inside=false;
constexpr unsigned kMaxTfClockSamples=18000;
std::atomic<unsigned> tf_poll_samples{0};
constexpr unsigned kMaxTfPollSamples=15000;

// Diagnostic ONLY. Emit bounded monotonic individual sleep spans from the
// same original TF call. Never emit source frames, poses or raw ROS messages.
void log_poll_sleep(long long t0,long long t1,long long req_ns,int rc) {
  if(t0<0 || t1<t0 || tf_poll_samples.fetch_add(1,std::memory_order_relaxed)
                     >=kMaxTfPollSamples) return;
  const int file=active_fd();
  if(file<0) return;
  char line[256];
  const int n=std::snprintf(line,sizeof(line),
    "TF_SLEEP pid=%ld tid=%ld mono_start_ns=%lld mono_end_ns=%lld req_ns=%lld rc=%d\n",
    static_cast<long>(::getpid()),static_cast<long>(::syscall(SYS_gettid)),
    t0,t1,req_ns,rc);
  if(n>0 && n<static_cast<int>(sizeof(line))) {
    (void)::write(file,line,static_cast<size_t>(n));
  }
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

// Native C++ Jazzy Clock::now symbol interposition. Some official CM
// library call sites resolve through the C++ member rather than through
// the C rcl_clock_get_now interposition observed by a standalone test.
// Delegate unchanged to the original exact C++ ABI and log READ ONLY only
// on the already-diagnostic official Advanced TF callback thread.
namespace rclcpp {
Time Clock::now() const
{
  using F=Time (*)(const Clock*);
  static F original=reinterpret_cast<F>(
      ::dlsym(RTLD_NEXT,"_ZNK6rclcpp5Clock3nowEv"));
  if(!original) std::abort();
  // Avoid duplicate C and C++ record output for the same original Clock.
  struct Suppress { Suppress(){tf_cpp_clock_inside=true;}
                    ~Suppress(){tf_cpp_clock_inside=false;} };
  Time now=[&](){Suppress guard;return original(this);}();
  const int saved_errno=errno;
  const bool track=tf_window_active &&
    tf_cpp_clock_samples.fetch_add(1,std::memory_order_relaxed)<kMaxTfClockSamples;
  if(track) {
    const int file=active_fd();
    if(file>=0) {
      const int typ=static_cast<int>(now.get_clock_type());
      const int active=typ==static_cast<int>(RCL_ROS_TIME) &&
        const_cast<Clock*>(this)->ros_time_is_active() ? 1:0;
      const long long mono=clock_ns(CLOCK_MONOTONIC);
      char line[240];
      const int n=std::snprintf(line,sizeof(line),
        "TF_CLOCK pid=%ld tid=%ld mono_ns=%lld ros_ns=%lld clock_type=%d override_active=%d\n",
        static_cast<long>(::getpid()),static_cast<long>(::syscall(SYS_gettid)),
        mono,static_cast<long long>(now.nanoseconds()),typ,active);
      if(n>0 && n<static_cast<int>(sizeof(line)))
        (void)::write(file,line,static_cast<size_t>(n));
    }
  }
  errno=saved_errno;
  return now;
}
}  // namespace rclcpp

// Other nodes/threads can preload this library but will not be measured.
// Nested libc nanosleep->clock_nanosleep wrappers count only the outer call.
extern "C" int nanosleep(const timespec* req,timespec* rem) noexcept {
  using F=int (*)(const timespec*,timespec*);
  static F next=reinterpret_cast<F>(::dlsym(RTLD_NEXT,"nanosleep"));
  if(!next) std::abort();
  const bool count=tf_window_active && tf_sleep_depth==0;
  ++tf_sleep_depth;
  const long long t0=count?clock_ns(CLOCK_MONOTONIC):-1;
  const int rc=next(req,rem);
  const int saved_errno=errno;
  const long long t1=count?clock_ns(CLOCK_MONOTONIC):-1;
  --tf_sleep_depth;
  if(count && t1>=t0 && t0>=0) {
    tf_sleep_wall_ns+=t1-t0;
    ++tf_sleep_calls;
    const long long request=req ?
      static_cast<long long>(req->tv_sec)*1000000000LL+req->tv_nsec : 0;
    log_poll_sleep(t0,t1,request,rc);
  }
  errno=saved_errno;
  return rc;
}
extern "C" int clock_nanosleep(clockid_t id,int flags,
                                const timespec* req,timespec* rem) noexcept {
  using F=int (*)(clockid_t,int,const timespec*,timespec*);
  static F next=reinterpret_cast<F>(::dlsym(RTLD_NEXT,"clock_nanosleep"));
  if(!next) std::abort();
  const bool count=tf_window_active && tf_sleep_depth==0;
  ++tf_sleep_depth;
  const long long t0=count?clock_ns(CLOCK_MONOTONIC):-1;
  const int rc=next(id,flags,req,rem);
  const int saved_errno=errno;
  const long long t1=count?clock_ns(CLOCK_MONOTONIC):-1;
  --tf_sleep_depth;
  if(count && t1>=t0 && t0>=0) {
    tf_sleep_wall_ns+=t1-t0;
    ++tf_sleep_calls;
    const long long request=(req && !(flags & TIMER_ABSTIME)) ?
      static_cast<long long>(req->tv_sec)*1000000000LL+req->tv_nsec : 0;
    log_poll_sleep(t0,t1,request,rc);
  }
  errno=saved_errno;
  return rc;
}

// The official Jazzy tf2_ros::Buffer::canTransform() obtains timeout time
// via rclcpp::Clock::now(), whose real implementation calls this C symbol.
// Observe the EXACT native CM thread during Advanced getTransform ONLY.
// No publishers, TF parameter changes, kernel scheduling or Nav2 fork.
extern "C" rcl_ret_t rcl_clock_get_now(
    rcl_clock_t* clock, rcl_time_point_value_t* time_point_value)
{
  using F=rcl_ret_t (*)(rcl_clock_t*,rcl_time_point_value_t*);
  static F next=reinterpret_cast<F>(::dlsym(RTLD_NEXT,"rcl_clock_get_now"));
  if(!next) std::abort();  // Fail closed when official ROS ABI absent.
  const bool count=tf_window_active && !tf_cpp_clock_inside &&
    tf_clock_samples.fetch_add(1,std::memory_order_relaxed)<kMaxTfClockSamples;
  const rcl_ret_t rc=next(clock,time_point_value);
  const int saved_errno=errno;
  if(count && rc==RCL_RET_OK && clock && time_point_value &&
      clock->type>=RCL_ROS_TIME && clock->type<=RCL_STEADY_TIME) {
    const int file=active_fd();
    if(file>=0) {
      int active=0;
      if(clock->type==RCL_ROS_TIME) {
        bool enabled=false;
        if(::rcl_is_enabled_ros_time_override(clock,&enabled)==RCL_RET_OK) {
          active=enabled ? 1 : 0;
        } else {
          // Unknown override is not evidence of active simulation time.
          active=0;
        }
      }
      const long long mono=clock_ns(CLOCK_MONOTONIC);
      char line[240];
      const int n=std::snprintf(line,sizeof(line),
        "TF_CLOCK pid=%ld tid=%ld mono_ns=%lld ros_ns=%lld clock_type=%d override_active=%d\n",
        static_cast<long>(::getpid()),static_cast<long>(::syscall(SYS_gettid)),
        mono,static_cast<long long>(*time_point_value),
        static_cast<int>(clock->type),active);
      if(n>0 && n<static_cast<int>(sizeof(line)))
        (void)::write(file,line,static_cast<size_t>(n));
    }
  }
  errno=saved_errno;
  return rc;
}

// True ABI selftest, no simulation/Goal: real official rcl_clock_get_now() is
// delegated and the nested diagnostic hook sees a tick on this thread.
extern "C" __attribute__((visibility("default")))
int axia_g07_task01_clock_get_now_abi_selftest() {
  const auto before=tf_clock_samples.load(std::memory_order_relaxed);
  rcl_clock_t c{};  // Jazzy rcl_clock_init requires zero-initialized storage.
  auto alloc=rcutils_get_default_allocator();
  if(rcl_clock_init(RCL_STEADY_TIME,&c,&alloc)!=RCL_RET_OK) return 0;
  rcl_time_point_value_t t=0;
  tf_window_active=true;
  const auto ret=rcl_clock_get_now(&c,&t);
  tf_window_active=false;
  (void)rcl_clock_fini(&c);
  return ret==RCL_RET_OK && t>0 &&
    tf_clock_samples.load(std::memory_order_relaxed)>before ? 1:0;
}

// This is the critical ABI regression. Direct calls to our own C shim
// alone do not prove that the official rclcpp::Clock::now() DSO dispatches
// through that shim. Exercise real Jazzy rclcpp::Clock::now() here, without
// any ROS node, simulator, or Goal.
extern "C" __attribute__((visibility("default")))
int axia_g07_task01_real_rclcpp_clock_dispatch_selftest() {
  const auto before=tf_clock_samples.load(std::memory_order_relaxed);
  const auto cpp_before=tf_cpp_clock_samples.load(std::memory_order_relaxed);
  rclcpp::Clock test_clock(RCL_ROS_TIME);
  tf_window_active=true;
  const auto now=test_clock.now();
  tf_window_active=false;
  return now.nanoseconds()>0 &&
    (tf_clock_samples.load(std::memory_order_relaxed)>before ||
     tf_cpp_clock_samples.load(std::memory_order_relaxed)>cpp_before) ? 1:0;
}

// Strict external ABI proof: intercept rclcpp::Clock::now itself, not
// just the C rcl_clock_get_now symbol called by our own test process.
extern "C" __attribute__((visibility("default")))
int axia_g07_task01_cpp_clock_dispatch_selftest() {
  const auto before=tf_cpp_clock_samples.load(std::memory_order_relaxed);
  rclcpp::Clock clock(RCL_ROS_TIME);
  tf_window_active=true;
  const auto now=clock.now();
  tf_window_active=false;
  return now.nanoseconds()>0 &&
    tf_cpp_clock_samples.load(std::memory_order_relaxed)>before ? 1:0;
}

// Isolated NO_GOAL selftest of the exact std::this_thread::sleep_for()
// path used by Jazzy tf2_ros::Buffer; never called by production Nav2.
extern "C" __attribute__((visibility("default")))
int axia_g07_s2_sleep_interposition_selftest() {
  tf_sleep_wall_ns=0;
  tf_sleep_calls=0;
  tf_sleep_depth=0;
  tf_window_active=true;
  std::this_thread::sleep_for(std::chrono::milliseconds(3));
  tf_window_active=false;
  return tf_sleep_calls>0 && tf_sleep_wall_ns>=1000000LL ? 1 : 0;
}

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
    tf_sleep_wall_ns=0;
    tf_sleep_calls=0;
    tf_window_active=true;
  }
  // The original official advanced transform is delegated unchanged.
  const bool ok=original(source_frame_id,source_time,target_frame_id,
                          target_time,fixed_frame_id,transform_tolerance,
                          tf_buffer,result);
  if(track) {
    tf_window_active=false;
    const long long c1=clock_ns(CLOCK_THREAD_CPUTIME_ID);
    const long long m1=clock_ns(CLOCK_MONOTONIC);
    const bool u1_ok=(::getrusage(RUSAGE_THREAD,&u1)==0);
    const bool sc1_ok=sc0_ok && thread_schedstat(sc1);
    const bool rusage_valid=(u0_ok && u1_ok &&
      u1.ru_nvcsw>=u0.ru_nvcsw && u1.ru_nivcsw>=u0.ru_nivcsw);
    const bool sched_valid=(sc1_ok &&
      sc1.runtime_ns>=sc0.runtime_ns &&
      sc1.wait_ns>=sc0.wait_ns && sc1.slices>=sc0.slices);
    const auto run_ns=sched_valid?sc1.runtime_ns-sc0.runtime_ns:0ULL;
    const auto delay_ns=sched_valid?sc1.wait_ns-sc0.wait_ns:0ULL;
    const long v=rusage_valid?u1.ru_nvcsw-u0.ru_nvcsw:0;
    const long iv=rusage_valid?u1.ru_nivcsw-u0.ru_nivcsw:0;
    char line[512];
    const int count=std::snprintf(line,sizeof(line),
      "TF_ADV pid=%ld tid=%ld mono_start_ns=%lld mono_end_ns=%lld thread_cpu_ns=%lld ok=%d schedstat_valid=%d runqueue_ns=%llu sched_cpu_ns=%llu voluntary_cs=%ld involuntary_cs=%ld sleep_ns=%lld sleep_calls=%u\n",
      static_cast<long>(::getpid()),static_cast<long>(::syscall(SYS_gettid)),
      m0,m1,c1-c0,ok?1:0,sched_valid?1:0,delay_ns,run_ns,v,iv,
      tf_sleep_wall_ns,tf_sleep_calls);
    if(count>0 && count<static_cast<int>(sizeof(line))) {
      (void)::write(file,line,static_cast<size_t>(count));
    }
  }
  return ok;
}
}  // namespace nav2_util
