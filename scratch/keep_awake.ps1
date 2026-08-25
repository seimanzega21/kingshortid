Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Awake {
    [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern uint SetThreadExecutionState(uint esFlags);
    public const uint ES_CONTINUOUS = 0x80000000;
    public const uint ES_SYSTEM_REQUIRED = 0x00000001;
    public const uint ES_DISPLAY_REQUIRED = 0x00000002;
}
"@

# ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
[Awake]::SetThreadExecutionState([Awake]::ES_CONTINUOUS -bor [Awake]::ES_SYSTEM_REQUIRED -bor [Awake]::ES_DISPLAY_REQUIRED) | Out-Null

Write-Host "PC is now locked in AWAKE state. Monitor and system will not sleep."
Write-Host "Keeping process alive to maintain the awake state..."

try {
    while ($true) {
        Start-Sleep -Seconds 3600
    }
} finally {
    # Restore normal state when script exits
    [Awake]::SetThreadExecutionState([Awake]::ES_CONTINUOUS) | Out-Null
    Write-Host "Restored normal sleep settings."
}
