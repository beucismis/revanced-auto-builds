# ReVanced Non-Root Builder

A sophisticated, automated pipeline that builds ready-to-install ReVanced applications for <strong>non-rooted Android devices</strong>. This system automatically fetches the latest ReVanced tools, downloads base APKs from multiple sources, applies patches, and publishes optimized APKs with architecture-specific builds.

## Quick Downloads

**Note:** All APKs are automatically rebuilt daily at 06:00 UTC to ensure you have the latest features and security patches.

### Download Links

| Mirror | Description | Link |
| :--- | :--- | :--- |
| **GitHub Releases** | Primary source. Contains all builds. | [**Download Latest Release**](https://RookieEnough/Revanced-AutoBuilds/releases/latest) |

### Supported Apps & Architectures

| Application | arm64-v8a | armeabi-v7a | Universal |
| :--- | :---: | :---: | :---: |
| **YouTube** | ✅ | ✅ | ✅ |
| **YouTube Music** | ✅ | ✅ | ❌ |
| **Reddit** | ❌ | ❌ | ✅ |
| **Twitter (X)** | ✅ | ❌ | ❌ |
| **TikTok** | ❌ | ❌ | ✅ |
| **Spotify** | ❌ | ❌ | ✅ |

*( Legend: ✅ = Available / ❌ = Not configured )*

## Key Features

This repository utilizes a robust Python-based pipeline to ensure high reliability and optimization.

* **Fully Automated:** GitHub Actions workflow executes daily at 06:00 UTC, requiring zero manual intervention.
* **Architecture Optimization:** Builds specific `arm64-v8a`, `armeabi-v7a`, and `universal` APKs to reduce file size and improve performance on target devices.
* **Multi-Source Strategy:** Intelligent fetching from APKMirror, APKPure, and Uptodown ensures high success rates even if one source is down.
* **Granular Patch Control:** Simple text-based configuration allows for precise inclusion or exclusion of specific patches.
* **Smart Failover:** The system automatically switches download sources if a fetch attempt fails.
* **Auto-Signing:** All APKs are signed with a consistent public keystore, making them ready to install immediately.
* **Clean Release Cycle:** Previous releases are replaced rather than archived, preventing clutter and making it easy for external managers (like Orion) to track updates.

## Repository Structure

```text
revanced-nonroot/
├── .github/workflows/      # GitHub Actions automation
│   ├── patch.yml           # Daily automated builds (06:00 UTC)
│   └── manual-patch.yml    # Manual trigger workflow
├── apps/                   # APK source configurations
│   ├── apkmirror/          # APKMirror definitions
│   ├── apkpure/            # APKPure definitions
│   └── uptodown/           # UptoDown definitions
├── patches/                # Patch inclusion/exclusion rules
├── sources/                # ReVanced tool source definitions
├── src/                    # Core Python build logic
├── arch-config.json        # Architecture build matrix
├── patch-config.json       # App build configuration
└── requirements.txt        # Project dependencies
```

## Configuration Guide

This builder is highly configurable. You can adjust the following files to customize the build output.

### 1. App Selection (`patch-config.json`)

Define which applications the pipeline should attempt to build.

```json
{
  "patch_list": [
    { "app_name": "youtube", "source": "revanced" },
    { "app_name": "youtube-music", "source": "revanced" },
    { "app_name": "twitter", "source": "revanced" }
  ]
}
```

### 2. Architecture Matrix (`arch-config.json`)

Specify which CPU architectures to target for each application.

```json
[
  {
    "app_name": "youtube",
    "source": "revanced",
    "arches": ["arm64-v8a", "armeabi-v7a", "universal"]
  },
  {
    "app_name": "youtube-music",
    "source": "revanced",
    "arches": ["arm64-v8a", "armeabi-v7a"]
  }
]
```

### 3. Source Definitions

Located in the `apps/` directory. Example for `apps/apkmirror/youtube.json`:

```json
{
  "org": "google-inc",
  "name": "youtube",
  "type": "APK",
  "arch": "universal",
  "dpi": "nodpi",
  "package": "com.google.android.youtube",
  "version": ""
}
```

### 4. Patch Rules

Located in `patches/`. Example for `patches/youtube-revanced.txt`. Use `+` to force include and `-` to exclude.

```text
# Essential patches
+ microg-support
+ premium-heading
+ hide-infocard-suggestions

# Exclusions
- custom-branding
- amoled
```

## Local Build Instructions

If you prefer to build the APKs on your own machine, follow these steps.

### Prerequisites

* Python 3.11 or higher
* Java Runtime Environment (JRE)
* `zip` utility
* `apksigner` (part of Android SDK Build-Tools)

### Installation & Execution

1. **Clone the repository:**
```bash
git clone https://github.com/RookieEnough/Revanced-AutoBuilds.git
cd revanced-nonroot
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
pip install requests beautifulsoup4
```

3. **Run the build:**
You can build for a specific app and source.
```bash
export APP_NAME="youtube"
export SOURCE="revanced"
python -m src
```

4. **Target specific architecture (Optional):**
```bash
export APP_NAME="youtube"
export SOURCE="revanced"
export ARCH="arm64-v8a"  # Options: arm64-v8a, armeabi-v7a, universal
python -m src
```

## GitHub Actions Workflows

### Daily Automated Build (`patch.yml`)

* **Schedule:** Runs daily at 06:00 UTC.
* **Function:** Iterates through all configured apps and architectures.
* **Output:** Updates the single "Latest" release tag.

### Manual Build (`manual-patch.yml`)

* **Trigger:** Manually via the GitHub Actions "Run workflow" button.
* **Capabilities:**
* Target specific apps.
* Target specific architectures.
* Force specific APK versions.
* Option to update the public release or just build artifacts.

## Contributing

Contributions to improve the toolchain or add support for new apps are welcome.

1. **Fork** the repository.
2. **Create** a feature branch (`git checkout -b feature/new-app`).
3. **Test** your changes locally using the Python scripts.
4. **Commit** your changes (`git commit -m "Add support for new-app"`).
5. **Push** to the branch (`git push origin feature/new-app`).
6. **Open** a Pull Request.

## Disclaimer & Legal

**Important:** This project is an automated build tool. The APKs provided in the releases are generated automatically using official ReVanced tools and patches.

* **Affiliation:** These builds are **not** officially affiliated with the ReVanced Team.
* **Usage:** Provided for educational and convenience purposes only. Use at your own risk.
* **GmsCore:** ReVanced GmsCore is required for these non-root apps to function correctly.
* **Updates:** Patches are automatically pulled from the latest sources; builds may occasionally contain experimental features.

