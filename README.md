# EeveePulse

**Studio light rigs with color harmonies, mood sampling, camera tracking, and procedural world dome for Blender EEVEE.**

![Blender](https://img.shields.io/badge/Blender-4.0%2B-orange)
![Version](https://img.shields.io/badge/Version-3.0.0-blue)
![License](https://img.shields.io/badge/License-GPL--3.0-green)

---

## Overview

**EeveePulse** is a studio lighting add-on for Blender 4.0+ designed to streamline three-point lighting workflows in **EEVEE** and **EEVEE Next**. Accessible from **View3D > Sidebar (`N`) > EeveePulse**, it automatically sizes and scales a three-point area light rig around your selected meshes, balances light energy using inverse-square distance compensation, and integrates color theory harmonies, image mood sampling, camera-locked relighting, and pulse keyframe animation.

---

## Key Features

* **Adaptive 3-Point Rig (`Generate Rig` / `Purge Rig`)**
  Computes the combined world-space bounding box of all selected mesh objects (or active mesh) to position **Key**, **Fill**, and **Rim** area lights around a central `EeveePulse_Target` empty with `TRACK_TO` constraints and inverse-square energy scaling. Re-generating preserves your rig's position and base dimensions when no new mesh is selected, while `Purge Rig` cleanly deletes all rig objects and orphaned data-blocks.
* **1-Click EEVEE Setup (`Optimize Engine`)**
  Switches the scene render engine to EEVEE Next (`BLENDER_EEVEE_NEXT` with `BLENDER_EEVEE` fallback), enables Screen Space Reflections and Refractions, and activates Contact Shadows on EeveePulse lights.
* **5 Built-In Lighting Presets**
  * **Neutral Studio** — Pure white, uncolored balanced three-point setup.
  * **Dramatic Noir** — High-contrast, moody lighting with complementary color harmony.
  * **Soft Commercial** — Balanced, low-contrast illumination with subtle analogous hues.
  * **Cyberpunk Neon** — High-saturation triadic neon lighting.
  * **High Key** — Bright, minimal-shadow studio lighting.
* **Real-Time Color Harmonies**
  Automatically computes Fill and Rim colors from your Key light color using **Off**, **Complementary**, **Triadic**, **Analogous**, or **Cinematic** (warm key / cool teal fill & rim) modes with an adjustable **Harmony Intensity** blend slider.
* **Mood Sampler**
  Samples the dominant color from any loaded reference image using fast pixel subsampling and applies it directly to the Key light.
* **Probes & Shadow Blockers**
  * **Auto Probes** — Automatically creates and scales an Irradiance Volume/Grid and Reflection Probe around your subject's bounding box.
  * **Auto Shadow Blockers** — Spawns wireframe, render-hidden blocker planes between the Key light and target at a configurable distance scale.
* **Camera Relighting (`Camera Lock`)**
  Dynamically repositions the Key, Fill, and Rim lights in camera space (`Right`, `Up`, `Forward`) as you move or orbit the active camera.
* **Animation & Pulse (`Bake Pulse` / `Clear Pulse`)**
  Bakes energy modulation keyframes across a custom frame range using **Sine**, **Breathe**, **Sawtooth**, or procedural **Noise** waveforms with adjustable frequency and amplitude, plus one-click keyframe removal.
* **Procedural Environment Dome (`Generate Studio World` / `Auto World Dome`)**
  Builds a vertical Z-gradient world shader blending between Key and Fill colors with live updates and strength control.

---

## Installation

1. Download the repository as a `.zip` file (**Code > Download ZIP**) or download the latest release archive.
2. Open Blender (`4.0` or newer) and navigate to **Edit > Preferences > Add-ons**.
3. Click **Install...** (or **Install from Disk...** in Blender 4.2+), select `EeveePulse.zip`, and click **Install Add-on**.
4. Enable **Lighting: EeveePulse** by checking the box next to its name.
5. Open the **3D Viewport**, press `N` to open the Sidebar, and select the **EeveePulse** tab.

---

## Quick Start

1. Select one or more mesh objects in your scene.
2. Open **View3D > Sidebar > EeveePulse** and click **Optimize Engine**.
3. Click **Generate Rig** to create the adaptive 3-point rig, target empty, and light probes.
4. Pick a look under **Presets** and click **Apply Preset**, or fine-tune **Key/Fill/Rim Intensity**, **Rig Scale Factor**, and **Harmony Mode**.
5. *(Optional)* Load a reference image in **Mood Sampler** and click **Sample Image Colors**, or enable **Auto World Dome** for matching ambient environment lighting.
6. Click **Purge Rig** at any time to remove all EeveePulse objects and clean up orphaned data-blocks.

---

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**. See the `LICENSE` file for details.
