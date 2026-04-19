#include "ProcessMemory.h"
#include <iostream>

#if defined(__APPLE__)
#include <mach/mach.h>

void printProcessMemory() {
    task_vm_info_data_t vm;
    mach_msg_type_number_t count = TASK_VM_INFO_COUNT;
    kern_return_t kr = task_info(mach_task_self(), TASK_VM_INFO,
                                 reinterpret_cast<task_info_t>(&vm), &count);
    if (kr == KERN_SUCCESS) {
        std::cout << "RSS: " << (vm.phys_footprint / 1024.0 / 1024.0) << " MB\n";
    } else {
        std::cout << "memory: n/a\n";
    }
}

#elif defined(_WIN32)
#include <windows.h>
#include <psapi.h>

void printProcessMemory() {
    PROCESS_MEMORY_COUNTERS pmc{};
    if (GetProcessMemoryInfo(GetCurrentProcess(), &pmc, sizeof(pmc))) {
        std::cout << "RSS: " << (pmc.WorkingSetSize / 1024.0 / 1024.0) << " MB\n";
    } else {
        std::cout << "memory: n/a\n";
    }
}

#else
#include <unistd.h>
#include <fstream>

void printProcessMemory() {
    std::ifstream f("/proc/self/statm");
    long total_pages = 0, rss_pages = 0;
    if (f && (f >> total_pages >> rss_pages)) {
        double mb = rss_pages * (getpagesize() / 1024.0 / 1024.0);
        std::cout << "RSS: " << mb << " MB\n";
    } else {
        std::cout << "memory: n/a\n";
    }
}
#endif