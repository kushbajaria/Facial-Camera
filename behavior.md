# Product Behavior Spec

This document defines exactly how the smart door camera behaves for homeowners, guests, and system safety. It is written as a product-ready baseline for implementation and testing.

## 1) Trigger and Capture
- Trigger: Motion detection starts the camera scan. Authorized users can walk up without ringing.
- Camera activation: Idle mode watches for motion; full recognition engages when motion is detected.
- Scan window: 8 seconds per attempt.
- Face detection retry: If no face is detected within 2 seconds, keep scanning for the full window and show "Please face the camera."
- Optional doorbell: If present, it can force an immediate scan and display visitor prompts.

## 2) Recognition and Decision
- Recognition threshold: Confidence < 70 (configurable).
- Authorized outcome:
  - Display: "Verified"
  - Audio: Short chime
  - Action: Unlock door
  - Duration: Unlock for 15 seconds (configurable)
  - Auto-lock: Lock after duration or on door-close sensor (if available)
- Unauthorized outcome:
  - Display: "Not recognized"
  - Audio: Short denial beep
  - Action: If door is unlocked, lock immediately. Otherwise remain locked.
  - Optional: Send notification with snapshot

## 3) UI and Feedback
- While scanning: Show "Scanning..." and progress indicator.
- After decision: Show result for 5 seconds, then return to idle scan.
- Manual close (debug only): Press Q to exit scan early.

## 4) Enrollment
- Admin only: Only the account owner can add users.
- Enrollment flow:
  - Capture 3 to 5 images per user (front, slight left/right)
  - Save user info and face data under the account
- Duplicate prevention: Warn if a new face looks similar to an existing user.

## 5) Access Roles
- Owner: Full control (add/remove users, change settings).
- Member: Can unlock.
- Guest: Optional, time-limited access.

## 6) Offline Behavior
- Default: All core features work without internet.
- Cloud features (optional): Notifications, remote unlock, and log sync.

## 7) Security
- Fail-secure: Default to locked on errors or reboot.
- Anti-spoofing (roadmap): Blink or depth check.
- Rate limiting: No more than 3 scans per minute if repeated failures.

## 8) Logging
- Local log: Timestamp, result, matched user (if any).
- Retention: 30 days (configurable).
- Export: Admin can export logs for audit.

## 9) Configuration
- Scan window duration
- Unlock duration
- Confidence threshold
- Notifications on or off
- Log retention period

## 10) Reliability
- Startup: System auto-launches on boot.
- Recovery: Auto-restart if the camera fails.
- Power loss: Door remains locked.
