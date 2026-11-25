# Standalone offline Samsung Galaxy S22 benchmark

A separate arm64 debug app measures the pinned DocAligner SA24 ONNX graph with ONNX Runtime Android 1.22.0 CPU. It requests no network permission and contains no weights or images. The host helper stages them in the benchmark app’s private data using ADB. The app has its own package and can coexist with MechaVision.

## Build and run

Install JDK 17, Android SDK Platform 35 and platform-tools. Use Gradle 8.9 or the corresponding Android Studio setup. Configure the Android SDK via `ANDROID_HOME` or an untracked `local.properties` in this directory. Dependency downloads are required for the first build. Use the pinned checkpoint from the [Python instructions](../README.md) and the same Python dependencies.

From the repository root, run the following with the S22 connected through USB debugging. On Windows supply your own paths instead of the shell variables and use its Gradle and Python executables.

```sh
gradle -p Tools/markerless_eval/android assembleDebug
adb devices
python -m Tools.markerless_eval.phone \
  --apk "$benchmark_apk" \
  --weights "$sa24" --image "$private_session_photo" \
  --threads 1 --warmup 5 --iterations 30 --output "$private_result_json"
```

The APK filename follows the Gradle project name. Use the actual `.apk` printed or generated under `build/outputs/apk/debug`. Leave the phone in airplane mode during the measurement if you want to verify the offline run. Use USB ADB and pass `--serial` if more than one device is present. The command creates the JSON only when the instrumented process reports results. It records source image dimensions but excludes the image itself.

## What is measured

The benchmark verifies the checkpoint checksum and byte size on device. It reports debug APK byte size, model session creation time, median and p95 for ONNX forward alone and for resize, RGB tensor creation, inference and heatmap materialization together. Android Bitmap resizing differs from desktop OpenCV. Image decoding is outside the timed iterations. The PSS readings sample the app before image decode and ORT initialization, after load, after warmup and after several additional runs. These are sampled process measurements with model and frame resident. They can miss transient peaks.

This app consumes a fixed EXIF-oriented frame and verifies the four-channel heatmap. The desktop corner extraction, grid validation, fallback proposals, camera frames, live tracking and Unity rendering are beyond its measurement scope. If the measured model-stage p95 already exceeds a 30 fps frame budget of about 33 ms, a serial per-frame pipeline cannot meet that budget. Use the full pipeline on the phone before judging intermittent acquisition, sustained tracking, or thermal behaviour. Record a cold-device run and another after the phone warms up. Return the JSONs if you want the CPU measurements included with the held-out report.

The Java source was type-checked in the cloud against Android API 35 classes and the ONNX Runtime Android 1.22.0 AAR. APK packaging and an S22 device run remain unverified.
