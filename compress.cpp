#include <filesystem>
#include <iostream>
#include <vector>
#include <thread>
#include <mutex>
#include <queue>
#include <cstdlib>

namespace fs = std::filesystem;

// -------- CONFIG --------
constexpr int MAX_GPU_JOBS = 2;      // Safe for M2 Pro
constexpr int DEFAULT_QUALITY = 5;
const std::string OUTPUT_ROOT = "compressed";
const std::string PRESET_NAME = "H.265 Apple VideoToolbox 1080p";
// ------------------------

std::mutex queueMutex;
std::queue<fs::path> jobs;

bool isVideoFile(const fs::path& p) {
    auto ext = p.extension().string();
    return ext == ".mp4" || ext == ".mov" || ext == ".mkv" || ext == ".m4v";
}

bool alreadyCompressed(const fs::path& p) {
    std::string s = p.string();
    return s.find("/" + OUTPUT_ROOT + "/") != std::string::npos ||
           (s.size() >= 15 && s.compare(s.size() - 15, 15, "_compressed.mp4") == 0);
}

void compressOne(const fs::path& input, bool singleFile, int quality) {
    if (alreadyCompressed(input)) {
        std::cout << "⏭ Skipping: " << input << "\n";
        return;
    }

    fs::path outDir = OUTPUT_ROOT;
    if (!singleFile)
        outDir /= input.parent_path();

    fs::create_directories(outDir);

    fs::path output =
        outDir / (input.stem().string() + "_compressed.mp4");

    std::cout << "🎞  " << input.filename() << "\n";

    std::string cmd =
        "HandBrakeCLI "
        "-i \"" + input.string() + "\" "
        "-o \"" + output.string() + "\" "
        "--preset \"" + PRESET_NAME + "\" "
        "-q " + std::to_string(quality) + " "
        "--all-audio --all-subtitles --markers --optimize";

    int rc = system(cmd.c_str());
    if (rc != 0) {
        std::cerr << "❌ HandBrake failed: " << input << "\n";
        return;
    }

    system(("touch -r \"" + input.string() + "\" \"" + output.string() + "\"").c_str());

    std::cout << "✅ Done → " << output << "\n";
}

void worker(bool singleFile, int quality) {
    while (true) {
        fs::path job;
        {
            std::lock_guard<std::mutex> lock(queueMutex);
            if (jobs.empty()) return;
            job = jobs.front();
            jobs.pop();
        }
        compressOne(job, singleFile, quality);
    }
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <file-or-dir> [quality]\n";
        return 1;
    }

    fs::path inputPath = argv[1];
    int quality = (argc >= 3) ? std::stoi(argv[2]) : DEFAULT_QUALITY;

    if (!fs::exists(inputPath)) {
        std::cerr << "❌ Invalid input\n";
        return 1;
    }

    bool singleFile = fs::is_regular_file(inputPath);

    if (singleFile) {
        jobs.push(inputPath);
    } else {
        for (fs::recursive_directory_iterator it(inputPath), end; it != end; ++it) {
            const auto& e = *it;
            if (e.is_directory() && e.path().filename() == OUTPUT_ROOT) {
                it.disable_recursion_pending();
                continue;
            }
            if (e.is_regular_file() && isVideoFile(e.path())) {
                jobs.push(e.path());
            }
        }
    }

    std::cout << "Found " << jobs.size() << " video(s)\n";

    std::vector<std::thread> threads;
    for (int i = 0; i < MAX_GPU_JOBS; ++i)
        threads.emplace_back(worker, singleFile, quality);

    for (auto& t : threads)
        t.join();

    std::cout << "🎉 All conversions complete.\n";
}
