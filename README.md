# Wwise Event Tapper (WwET)

## Context

On 2025-07-17 I learned from Muchan about his 3D rhythm game project.

They needed an _event tapper_ to batch-produce Wwise events efficiently,
preferably with a GUI agnostic to engines, because they want to reuse the tool
for non-Unity projects too.

## Structure

- `headless`: UI-agnostic components.
- `service`: integrate components into business use cases.
- `window`: dispatch user events and present service results.

## Passes

### The Crude Pass

The first happy path of the app is to play music, capture taps with the music
offset and store somewhere. The stored _tap data_ can be further calibrated,
and then pipelined into a Wwise project.

I'll build this PoC with _PySide6_, a cross-platform GUI framework for Python.
