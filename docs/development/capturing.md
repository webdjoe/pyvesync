# Packet Capturing for New Device Support

This document outlines the steps to capture network packets for adding support for new devices in the `pyvesync` library. It is intended for developers who want to extend the library's functionality by integrating additional VeSync devices. Packet captures are required in order to add new devices and functionality.

The process outlined below is time consuming and can be difficult. An alternative method is to temporarily share the device. If you would prefer this method, please indicate in an issue or contact the maintainer directly. Sharing a device is done by going to the device settings and selecting "Share Device". Please create a post to notify the maintainers to receive the correct email address to share the device with.

Please do not post a device request without being will to either capture packets or share the device.

## Prerequisites

1. **Mumu Emulator**: Download and install the Mumu Android emulator from [Mumu Player](https://www.mumuplayer.com/). This emulator allows you to run Android apps on your computer. Other emulators may work, but Mumu is known to be compatible with Arm64 apk's and allows `adb root` access.

2. **VeSync App**: The latest VeSync app from apkpure or another apk sharing site.

3. **Charles Proxy**: Download and install Charles Proxy from [Charles](https://www.charlesproxy.com/). The 30
day trial is sufficient for this purpose. If you do like the software, support the developer by purchasing a license.

4. **ADB (Android Debug Bridge)**: Ensure you have ADB installed on your system. This is typically included with Android Studio, but can also be installed separately with Android Command Line Tools. This is the site for [Android Studio](https://developer.android.com/studio). Scroll to the "Command Line Tools Only" section to download just the command line tools. Once installed, ensure adb is in your system PATH. You may have to restart your terminal or IDE to pick up the PATH change. The following path is where the `adb` binary is located: `C:\Users\YOUR_USERNAME\AppData\Local\Android\Skd\platform-tools` on Windows or `/home/YOUR_USERNAME/Android/Sdk/platform-tools` on Linux.

5. **frida-server**: Download the latest frida-server from [frida-server](https://github.com/frida/frida/releases). Choose the release that matches the architecture of the MuMu emulator - `frida-server-x.x.x-android-x86_x64.xz`. Extract the `frida-server` binary and place it in the project directory.

## Steps

1. **Set up project directory**:
   - Create a new directory for the project and place the extracted `frida-server` binary in it.
   - Move the VeSync (x)apk to the project directory.
   - Open a terminal in the project directory.
   - Create a virtual environment and install frida:

      ```bash
         python -m venv venv
         source venv/bin/activate
         # On Windows cmd use `venv\Scripts\activate`
         # On powershell use `venv\Scripts\Activate.ps1`
         pip install frida-tools
      ```

2. **Set up Charles Proxy**:
    - Open Charles Proxy and go to `Proxy` > `Proxy Settings`. Note the HTTP Proxy port (default is 8888).
    - Go to `Help` > `SSL Proxying` > `Save Root Certificate` > `cert format`.
    - Save the certificate to the project directory as `cert-der.crt`.

3. **Set up MuMu Emulator**:
    - Open the Mumu emulator and install the VeSync app by using the down arrow icon on the top right. Select "Install APK" from the bottom of the menu and choose the VeSync apk in the project directory.
    - Configure the proxy in `System Applications` > `Settings` > `Network & Internet` > `Internet` > Gear icon next to the connected network. If charles is running on the same machine, set the proxy hostname to `localhost:8888` (or the port you noted earlier).
    - Enable SSL Proxying in Charles by going to `Proxy` > `SSL Proxying Settings` and checking `Enable SSL Proxying`. Add a location with Host: `*` and Port: `*` if not already set.

4. **Configure MuMu to use Charles Proxy**:
    - Once the MuMu emulator is running, open a new terminal in the project directory and run:

    ```bash
       adb connect 127.0.0.1:7555
       adb root
       adb push cert-der.crt /data/local/tmp/
       adb push frida-server /data/local/tmp/
       adb shell

       # This should bring up the android emulator command line
       cd /data/local/tmp
       chmod +x frida-server
       ./frida-server
    ```

    - **LEAVE THIS TERMINAL OPEN**. There will be no output from the final command.

5. **Run the frida script**:
   - With Mumu and the frida-server terminal running, open a separate terminal in the project directory, and ensure that the virtual environment is activated.
   - Run the following command to start frida with the VeSync app:

   ```bash
      frida -U --codeshare akabe1/frida-multiple-unpinning -f com.etekcity.vesyncplatform
   ```

   - This will start the VeSync app and allow charles to capture the packets. You should see output in the terminal indicating that frida has attached to the process and the app will open in the emulator.
   - Login to your VeSync account in the app and check that charles is able to capture and decode the packages. The url should start with `https://smartapi.vesync.com` or `https://smartapi.vesync.eu`. On occasion it may start with `https://smartapi.vesyncapi.com` or `https://smartapi.vesyncapi.eu`.

6. **Run actions in the VeSync app**:
   - Perform all of the actions, including timers and schedulers. Ensure that after each action you go back to the device list and then back into the device. This ensures that the status of the device is captured after each action.
   - If you have multiple devices, perform actions on each device.

7. **Save the Charles session**:
   - Once all actions have been performed, stop the frida process by pressing `CTRL+C` in the frida terminal.
   - In Charles, go to `File` > `Save Session As...` and save the session as `vesync_session.chls` in the project directory.

8. **Share the capture**:
   - **DO NOT** post the capture in an issue. Please create an issue or comment on an issue to notify the maintainers that you have a capture ready to share.
   - Files can be shared via discord or email to webdjoe at gmail.
