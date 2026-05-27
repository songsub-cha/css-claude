plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.example.toy"
    compileSdk = 34
    defaultConfig {
        applicationId = "com.example.toy"
        minSdk = 24
        targetSdk = 34
    }
    buildFeatures { compose = true }
}

dependencies {
    implementation("androidx.activity:activity-compose:1.9.0")
    implementation("androidx.compose.ui:ui:1.6.0")
    implementation("androidx.compose.material3:material3:1.2.0")
    testImplementation("junit:junit:4.13.2")
}
