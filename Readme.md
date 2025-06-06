# EXADPrinter : Exhaustive Permissionless Device Fingerprinting Within the Android Ecosystem

This repository contains essential materials for  IEEE Computer Society's Technical Community on Security and Privacy.

Submission #338 

## 📦 Contents
### [`fingerprintinglib`](fingerprintinglib)

This directory contains the source code used for device fingerprint extraction. It is implemented as an Android library package written in **Kotlin**, and includes **10 classes** that work together to extract attributes using three main techniques: **Shell Command Execution**, **Java Reflection**, and **Content Provider Inspection**.

Below is a description of the key classes:

- [`FingerprintExtractor.kt`](fingerprintinglib/src/main/java/com/exadprinter/fingerprintinglib/FingerprintExtractor.kt):  
  Contains the core logic for attribute extraction. It coordinates the three extraction techniques in the following order: executes shell commands, extracts SDK attributes via reflection, and finally queries content providers.

- [`ShellCommandsExplorer.kt`](fingerprintinglib/src/main/java/com/exadprinter/fingerprintinglib/ShellCommandsExplorer.kt):  
  Manages the list of shell commands to execute and contains the logic for their execution.

- [`SDKExplorer.kt`](fingerprintinglib/src/main/java/com/com.exadprinter/fingerprintinglib/SDKExplorer.kt):  
  Handles the inspection of Android native APIs via reflection. It begins by loading a JSON file of documented classes and initializing the `InstanceFactory`, which creates object instances. This process uses the `SystemServiceFactory` to access available system services via the `Context` class, after which it extracts fields and invokes methods.

- [`ContentProviderExplorer.kt`](fingerprintinglib/src/main/java/com/exadprinter/fingerprintinglib/ContentProviderExplorer.kt):  
  Responsible for querying a predefined list of content provider URIs and collecting their exposed values.

- [`InstanceFactory.kt`](fingerprintinglib/src/main/java/com/exadprinter/fingerprintinglib/InstanceFactory.kt) and  
  [`SystemServiceFactory.kt`](fingerprintinglib/src/main/java/com/exadprinter/fingerprintinglib/SystemServiceFactory.kt):  
  Provide object instantiation logic for SDK classes and access to Android system services, respectively.

- [`FingerprintingUtils.kt`](fingerprintinglib/src/main/java/com/exadprinter/fingerprintinglib/FingerprintingUtils.kt):  
  Contains utility methods used throughout the fingerprinting process.

- [`RootChecker.kt`](fingerprintinglib/src/main/java/com/exadprinter/fingerprintinglib/RootChecker.kt):  
  Checks whether the device is rooted.

#### How to use [`fingerprintinglib`](fingerprintinglib) ? 

1. Import the library in your `build.gradle` file of your project : 
```gradle
dependencies {
    implementation project(":fingerprintinglib")
    ...
}
```

2. Create attributes extractors and call extract fingerprint 
```java
val adbExplorer = ShellCommandsExplorer(...)
val classesList = ClassesJsonReader().readJsonFromAssets(applicationContext)
val instanceFactory = InstanceFactory(applicationContext)
val sdkExplorer = SDKExplorer(instanceFactory, classesList,...)
val contentProviderExplorer = ContentProviderExplorer(applicationContext,...)
val fingerprintExtractor = FingerprintExtractor(sdkExplorer, adbExplorer, contentProviderExplorer, applicationContext)

// Extract fingerprint
fingerprintExtractor.extractFingerprint()
```

### [`data_analysis_scripts`](data_analysis_scripts)

This directory contains the source code used for preprocessing the dataset and computing fingerprint uniqueness and stability.

- [`data_preparation_pipeline.ipynb`](data_analysis_scripts/data_preparation_pipeline.ipynb):  
  A Jupyter notebook implementing the preprocessing pipeline. It iterates over all collected fingerprints stored in archive files, extracts the `data.json` content, and parses it using the [`fingerprint_parser`](data_analysis_scripts/fingerprint_parser) module.

  The `fingerprint_parser` module includes three specialized classes for parsing different attribute sources:
  - [`cp_attributes_parser.py`](data_analysis_scripts/fingerprint_parser/cp_attributes_parser.py): Parses content provider attributes.
  - [`sdk_attributes_parser.py`](data_analysis_scripts/fingerprint_parser/sdk_attributes_parser.py): Parses attributes extracted via SDK reflection.
  - [`shell_attributes_parser.py`](data_analysis_scripts/fingerprint_parser/shell_attributes_parser.py): Parses shell command outputs.

  The parsed output for each fingerprint is saved as a JSON file inside the `PREPARE_DIR` directory.

- [`data_cleanning_pipeline.ipynb`](data_analysis_scripts/data_cleanning_pipeline.ipynb):  
  A Jupyter notebook implementing the attribute cleaning logic. It removes constant, redundant, and unstable attributes to generate two cleaned attribute sets:  
  - `top_cleaned_stable_attribute_entropies.csv`: Contains attributes with entropy > 0.5 that are stable on at least one device.  
  - `top_cleaned_all_stable_attribute_entropies.csv`: Contains attributes that are stable across all devices and have high entropy.

- [`fingerprint_uniqueness_pipeline.ipynb`](data_analysis_scripts/fingerprint_uniqueness_pipeline.ipynb):  
  A Jupyter notebook that computes fingerprint uniqueness using the two cleaned attribute sets. It selects the best attribute combinations that maximize uniqueness and visualizes the results.



