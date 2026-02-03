// Copyright (c) 2016, DarkShock
// Copyright (c) 2019, qwertymodo
// Copyright (c) 2021, Cthulhu
//
// Redistribution and use in source and binary forms,
// with or without modification,
// are permitted provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice,
//    this list of conditions and the following disclaimer.
// 
// 2. Redistributions in binary form must reproduce the above copyright notice,
//    this list of conditions and the following disclaimer in the documentation
//    and/or other materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
// THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
// FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
// IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
// ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
// (INCLUDING, BUT NOT LIMITED TO,
// PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
// LOSS OF USE, DATA, OR PROFITS;
// OR BUSINESS INTERRUPTION)
// HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
// WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
// EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

scope Version {
    constant MAJOR(1)
    constant MINOR(1)
    constant PATCH(4)
}

arch snes.cpu

constant null(0)

// Boolean constants
constant false(0)
constant true(1)

scope Mode {
    // Addressing modes.
    constant DIR(0)  // Direct
    constant ABS(1)  // Absolute
    constant LONG(2) // Long
}

scope Register {
    constant P($01)
    constant A($02)
    constant X($04)
    constant Y($08)
    constant D($10)
    constant B($20)
    constant ALL(P|A|X|Y|D|B)

    macro save(variable registers) {
        if registers < 0 {
            error "Invalid registers for Register.save."
        } else if !registers {
            warning "No registers to save."
        }

        variable pflag($00)

        if (Register.A|Register.D) & registers {
            pflag = pflag | $20
        }
        if (Register.X|Register.Y) & registers {
            pflag = pflag | $10
        }

        if Register.P & registers {
            php
        }

        if pflag {
            rep #pflag
        }

        if Register.A & registers {
            pha
        }
        if Register.X & registers {
            phx
        }
        if Register.Y & registers {
            phy
        }
        if Register.D & registers {
            phd
            direct(Memory.PAGE)
        }

        if pflag {
            sep #pflag
        }

        if Register.B & registers {
            phb
            absolute($00)
        }
    }

    macro restore(variable registers) {
        if registers < 0 {
            error "Invalid registers for Register.restore."
        } else if !registers {
            warning "No registers to restore."
        }

        variable pflag($00)

        if Register.A & registers {
            pflag = pflag | $20
        }
        if (Register.X|Register.Y) & registers {
            pflag = pflag | $10
        }

        if pflag {
            rep #pflag
        }

        if Register.B & registers {
            plb
        }
        if Register.D & registers {
            pld
        }
        if Register.Y & registers {
            ply
        }
        if Register.X & registers {
            plx
        }
        if Register.A & registers {
            pla
        }
        if Register.P & registers {
            plp
        }
    }
}

scope Memory {
    constant BANK($7E0000)
    constant PAGE($1E00)

    macro load(variable mode, variable data, variable to) {
        if to == Register.A {
            define instruction(lda)
        } else if to == Register.X {
            define instruction(ldx)
        } else if to == Register.Y {
            define instruction(ldy)
        } else {
            error "Invalid register for Memory.load."
        }

        if mode == Mode.DIR {
            {instruction}.b data
        } else if mode == Mode.ABS {
            {instruction}.w Memory.PAGE | data
        } else if mode == Mode.LONG {
            {instruction}.l Memory.BANK | Memory.PAGE | data
        } else {
            error "Invalid addressing mode for Memory.load."
        }
    }

    macro store(variable mode, variable from, variable data) {
        if from == Register.A {
            define instruction(sta)
        } else if from == Register.X {
            define instruction(stx)
        } else if from == Register.Y {
            define instruction(sty)
        } else {
            error "Invalid register for Memory.store."
        }

        if mode == Mode.DIR {
            {instruction}.b data
        } else if mode == Mode.ABS {
            {instruction}.w Memory.PAGE | data
        } else if mode == Mode.LONG {
            {instruction}.l Memory.BANK | Memory.PAGE | data
        } else {
            error "Invalid addressing mode for Memory.store."
        }
    }

    macro clear(variable mode, variable data) {
        if mode == Mode.DIR {
            stz.b data
        } else if mode == MODE.ABS {
            stz.w Memory.PAGE | data
        } else {
            error "Invalid addressing mode for Memory.clear."
        }
    }
}

scope SNES {
    scope MUL {
        // SNES multiplication registers.
        constant MULTIPLICAND($4202)
        constant MULTIPLIER($4203)
        constant PRODUCT_L($4216)
        constant PRODUCT_H($4217)
    }

    scope DIV {
        // SNES division registers.
        constant DIVIDEND_L($4204)
        constant DIVIDEND_H($4205)
        constant DIVISOR($4206)
        constant QUOTIENT_L($4214)
        constant QUOTIENT_H($4215)
        constant REMAINDER_L($4216)
        constant REMAINDER_H($4217)
    }

    scope SPC {
        // SPC communication ports.
        constant COMM0($2140)
        constant COMM1($2141)
        constant COMM2($2142)
        constant COMM3($2143)

        scope Game {
            // Variable addresses
            constant COMMAND($00)
            constant SOUND_REQUEST($01)
            constant FADE_TIME($01)
            constant FADE_VOLUME($02)
            constant BANK_REQUEST($10)

            scope Commands {
                // Constants
                constant PLAY($10)
                constant RESUME($11)
                constant INTERRUPT($14)
                constant FADE($80)
                constant STOP($F0)
                constant PAUSE($F5)
            }

            scope Echo {
                constant LIMIT($07)
                constant VALUE($05)
            }
        }
    }
}

scope MSU {
    // MSU memory map I/O.

    scope Input {
        constant STATUS($2000)
        constant READ($2001)
        constant ID($2002)
    }

    scope Output {
        constant SEEK($2000)
        constant TRACK_L($2004)
        constant TRACK_H($2005)
        constant VOLUME($2006)
        constant CONTROL($2007)
    }

    scope Flags {
        scope Status {
            constant TRACK_MISSING($08)
            constant AUDIO_PLAYING($10)
            constant AUDIO_REPEATING($20)
            constant AUDIO_BUSY($40)
            constant DATA_BUSY($80)
        }

        scope Control {
            constant AUDIO_STOP($00)
            constant AUDIO_PLAY($01)
            constant AUDIO_REPEAT($02)
            constant AUDIO_RESUME($04)
        }
    }

    scope Values {
        scope Status {
            constant REVISION1($01)
            constant REVISION2($02)
        }

        scope ID {
            constant VALUE($532D4D535531) // S-MSU1
            constant SIZE($06)
        }

        scope Volume {
            constant EMPTY($00)
            constant FULL($FF)
        }
    }

    macro check(variable mode, variable fallback) {
        if mode == Mode.ABS {
            define suffix(w)
        } else if mode == Mode.LONG {
            define suffix(l)
        } else {
            error "Invalid addressing mode for MSU.check."
        }

        rep #$20

        variable offset($00)

        while offset < MSU.Values.ID.SIZE {
            variable idchunk((MSU.Values.ID.VALUE >> (((MSU.Values.ID.SIZE - 2) - offset) << 3)) & $FFFF)
            idchunk = ((idchunk << 8) | (idchunk >> 8)) & $FFFF // Swap bytes for little endianness.

            lda.w #idchunk
            cmp.{suffix} MSU.Input.ID+offset
            bne fallback

            offset = offset + 2
        }

        sep #$20
    }

    macro status(variable mode) {
        if mode == Mode.ABS {
            lda.w MSU.Input.STATUS
        } else if mode == Mode.LONG {
            lda.l MSU.Input.STATUS
        } else {
            error "Invalid addressing mode for MSU.status."
        }
    }

    macro missing(variable mode, variable fallback) {
        MSU.status(mode)
        bit.b #MSU.Flags.Status.TRACK_MISSING
        beq fallback
    }

    macro not_missing(variable mode, variable fallback) {
        MSU.status(mode)
        bit.b #MSU.Flags.Status.TRACK_MISSING
        bne fallback
    }

    macro playing(variable mode, variable fallback) {
        MSU.status(mode)
        bit.b #MSU.Flags.Status.AUDIO_PLAYING
        beq fallback
    }

    macro not_playing(variable mode, variable fallback) {
        MSU.status(mode)
        bit.b #MSU.Flags.Status.AUDIO_PLAYING
        bne fallback
    }

    macro repeating(variable mode, variable fallback) {
        MSU.status(mode)
        bit.b #MSU.Flags.Status.AUDIO_REPEATING
        beq fallback
    }

    macro not_repeating(variable mode, variable fallback) {
        MSU.status(mode)
        bit.b #MSU.Flags.Status.AUDIO_REPEATING
        bne fallback
    }
}

scope Tracklist {
    constant ADDRESS($CD5D20) // 449 bytes block starting at $CD5D05.
    constant MAX_SIZE(422)    // Maximum address space.

    constant SIZE(85)
    constant EXTRAS(1) // Extra tracks that are not in the original game.

    scope Actions {
        constant NONE($FF)
        constant STOP(MSU.Flags.Control.AUDIO_STOP)
        constant PLAY(MSU.Flags.Control.AUDIO_PLAY)
        constant LOOP(MSU.Flags.Control.AUDIO_PLAY|MSU.Flags.Control.AUDIO_REPEAT)
    }

    scope Fade {
        constant IN_THRESHOLD($10)
    }

    scope Tracks {
        constant THEME($18)
        constant THEME_ATTRACT($54)
    }
}

scope Patch {
    constant ADDRESS($CDF9D0) // 1607 bytes block starting at $CDF9B9.
    constant MAX_SIZE(1584)   // Maximum address space.

    scope Flags {
        // SPC
        constant SPC_MUTED($01)

        // Game
        constant GAME_STARTED($02)

        // MSU-1
        constant MSU_AUDIO_STARTED($10)

        constant MSU_SEMI($20) // MSU-1 with no resume support.
        constant MSU_FULL($40) // MSU-1 with resume support.
        constant MSU_UNSUPPORTED($80)
    }

    // RAM variable addresses used by this patch.
    constant FLAGS($E0) // 8-bits

    scope Track {                 // 5 bytes ($7E1EE1 - $7E1EE5)
        constant CURRENT($E1)     // 8-bits
        constant VOLUME($E2)      // 8-bits
        constant FADE_VOLUME($E3) // 8-bits
        constant FADE_STEP($E4)   // 8-bits
        constant VOLUME_GAIN($E5) // 8-bits
    }
}

macro print_hex(variable number, variable length) {
    // Prints a number as a hexadecimal string to the console.
    if length > 0 {
        putchar('$')

        while length {
            length = length - 1
            variable value((number >> (length << 2)) & $F)

            if value < $A {
                putchar('0'+value)
            } else {
                putchar('A'+(value - $A))
            }
        }
    } else {
        warning "print_hex called with an invalid length."
    }
}

macro seek(variable address) {
    variable bank((address >> 16) & $FF)
    variable page(address & $FFFF)

    if {defined EX} {
        if (bank >= $00 && bank <= $7D) {
            // ExHiROM section
            // No FastROM support.
            if bank < $40 && page < $8000 {
                error "Invalid ExHiROM address for seek."
            }

            origin address | $400000
            base address
        } else if (bank >= $80 && bank <= $FF) {
            // HiROM section
            // FastROM support.
            if bank < $C0 && page < $8000 {
                error "Invalid HiROM address for seek."
            }

            origin address & $3FFFFF
            base address
        } else {
            error "Invalid ExHiROM address for seek."
        }
    } else {
        if (bank >= $00 && bank <= $3F) || (bank >= $80 && bank <= $BF) {
            if page < $8000 {
                error "Invalid HiROM address for seek."
            }

            origin address & $3FFFFF
            base address | $800000 // Move address to FastROM address.
        } else if (bank >= $40 && bank <= $7D) || (bank >= $C0 && bank <= $FF) {
            origin address & $3FFFFF
            base address | $800000 // Move address to FastROM address.
        } else {
            error "Invalid HiROM address for seek."
        }
    }
}

macro assert(string name) {
    variable dataStart(ADDRESS)
    variable dataEnd(pc())
    variable dataSize(dataEnd - dataStart)

    print "data: {name} -> ",dataSize,"/",MAX_SIZE," bytes ("
    print_hex(dataStart, 6)
    putchar('-')
    print_hex(dataEnd, 6)
    print ")\n"

    if !dataSize {
        notice "No data written!"
    } else if dataSize > MAX_SIZE {
        error "Data is too big for this address space."
    }
}

macro direct(variable page) {
    // Set the direct page register to page.
    if page < 0x0000 || page > 0xFFFF {
        error "Invalid page for direct."
    }

    lda.w #page
    tcd
}

macro absolute(variable bank) {
    // Set the data bank register to bank.
    if bank < 0x00 || bank > 0xFF {
        error "Invalid bank for absolute."
    }
    
    lda.b #bank
    pha
    plb
}

macro return(variable source, variable offset) {
    // Return after jml.
    jml source+4+offset // jml length is 4.
}

// ========================
// = Original code hijack =
// ========================
scope Hooks {
    seek($C70004)
    MAIN:
        jml Patch.Main

    seek($00FF10)
    NMI:
        jml Patch.NMI

    if {defined EX} {
    seek($80FF10)
    NMI_OLD:
        jml Patch.NMI
    }

    seek($C70409)
    SPC_MUTE:
        jml Patch.SPCMute

    seek($C70A4B)
    SPC_ECHO:
        jml Patch.SPCEcho

    seek($C2CBE0)
    WAIT_TRACK_START1:
        jsl Patch.WaitTrackStart
        wdm #null
        wdm #null

    if {defined FRENCH} {
    seek($C33569)
    WAIT_TRACK_START2:
        jsl Patch.WaitTrackStart
        wdm #null
        db $34
        nop
    } else {
    seek($C335AF)
    WAIT_TRACK_START2:
        nop
        db $80
        jsl Patch.WaitTrackStart
        wdm #null
    }

    seek($C03CC6)
    WAIT_TRACK_FINISH:
        jml Patch.WaitTrackFinish
        nop

    seek($C00D00)
    GAME_START:
        jml Patch.GameStart

    // Allow SPC code to be overwritten via the data upload protocol.
    // NOTE: May have side effects affecting SPC addresses $0A00-1DFF.
    seek($C73306)
    DATA_UPLOAD_PROTOCOL:
        db $0A
}

// ============
// = MSU Code =
// ============
scope Patch {
seek(ADDRESS)

// Header
db "MSU-1 MUSIC",null

db Version.PATCH
db Version.MINOR
db Version.MAJOR

if {defined EX} {
    db true
} else {
    db false
}

scope Main: {
    Register.save(Register.P|Register.A|Register.D)

    lda.b #(Flags.MSU_SEMI|Flags.MSU_FULL)
    bit.b FLAGS
    bne MSUSupport
    bmi Default

    MSU.check(Mode.LONG, ++)

    MSU.status(Mode.LONG)
    and.b #$07 // Read the first 3 lower bits (revision).
    beq ++ // Revision 0?
    cmp.b #MSU.Values.Status.REVISION1
    beq +

    // Revision 2 or above.
    // Store the flag so we don't have to check for MSU-1 support everytime.
    lda.b #Flags.MSU_FULL
    tsb.b FLAGS

    bra MSUSupport
+
    // Revision 1.
    // Store the flag so we don't have to check for MSU-1 support everytime.
    lda.b #Flags.MSU_SEMI
    tsb.b FLAGS

    bra MSUSupport
+
    // MSU-1 not supported.
    // Store the flag so we don't have to check for MSU-1 support everytime.
    sep #$20
    lda.b #Flags.MSU_UNSUPPORTED
    tsb.b FLAGS

Default:
    Register.restore(Register.P|Register.A|Register.D)

    // Original routine
    jml $C70140

MSUSupport:
    lda.b SNES.SPC.Game.COMMAND

    // Play
    cmp.b #SNES.SPC.Game.Commands.PLAY
    beq +

    // Resume
    cmp.b #SNES.SPC.Game.Commands.RESUME
    beq +

    // Interrupt
    cmp.b #SNES.SPC.Game.Commands.INTERRUPT
    beq InterruptTrack

    // Pause/unpause during battle
    cmp.b #SNES.SPC.Game.Commands.PAUSE
    beq PauseTrack

    and.b #$FE

    // Fade
    cmp.b #SNES.SPC.Game.Commands.FADE
    beq FadeTrack

    // Stop
    cmp.b #SNES.SPC.Game.Commands.STOP
    bne Default
    stz.b SNES.SPC.Game.FADE_VOLUME
    bra FadeTrack
+
    jmp PlayTrack

    scope InterruptTrack: {
        // Is it the same track?
        lda.b Track.CURRENT
        beq +
        cmp.b SNES.SPC.Game.SOUND_REQUEST
        beq +

        bit.b FLAGS
        bvc + // Only revision 2 supports resume.

        lda.b #MSU.Flags.Control.AUDIO_RESUME
        sta.l MSU.Output.CONTROL
    +
        jmp PlayTrack
    }

    scope PauseTrack: {
        // Do we have a track playing to pause/unpause?
        lda.b Track.CURRENT
        beq Default

        lda.b #Flags.MSU_AUDIO_STARTED
        bit.b FLAGS
        beq Default

        lda.b SNES.SPC.Game.SOUND_REQUEST
        beq .Unpause
        cmp.b #SNES.SPC.Game.Commands.PAUSE
        bne Default

    .Pause:
        lda.b #MSU.Flags.Control.AUDIO_STOP
        sta.l MSU.Output.CONTROL

        jmp Default

    .Unpause:
        Register.save(Register.X|Register.Y)

        ldx.b Track.CURRENT
        lda.l Tracklist.ADDRESS,x
        sta.l MSU.Output.CONTROL

        Register.restore(Register.X|Register.Y)

        jmp Default
    }

    scope FadeTrack: {
        Register.save(Register.X|Register.Y|Register.B)

        lda.b Track.FADE_VOLUME
        bne +
        cmp.b SNES.SPC.Game.FADE_VOLUME
        beq ++
        cmp.b Track.VOLUME
        beq +

        stz.w MSU.Output.CONTROL
        stz.w MSU.Output.VOLUME

        stz.b Track.CURRENT
        stz.b Track.VOLUME
    +
        lda.b SNES.SPC.Game.FADE_VOLUME
        sta.b Track.FADE_VOLUME
    +
        cmp.b Track.VOLUME
        beq .SetVolume
        ldy.b SNES.SPC.Game.FADE_TIME
        bne .Compute
        sta.b Track.VOLUME

    .SetVolume:
        // Instant volume change.
        ldx.b Track.CURRENT
        beq .Exit

        tay

        lda.b #Flags.SPC_MUTED
        bit.b FLAGS
        beq .Exit

        lda.b Track.VOLUME_GAIN
        sta.w SNES.MUL.MULTIPLICAND
        sty.w SNES.MUL.MULTIPLIER

        // 8 cycles needed for the multiplication results.
        lda.b #Flags.MSU_AUDIO_STARTED // 2 cycles.
        bit.b FLAGS                    // 3 cycles.
        bne +                          // 2/3 cycles.

        // Attempt delayed track load.
        cpy.b #Tracklist.Fade.IN_THRESHOLD
        bcc .Exit

        tsb.b FLAGS

        lda.w SNES.MUL.PRODUCT_H
        sta.w MSU.Output.VOLUME

        lda.l Tracklist.ADDRESS,x
        sta.w MSU.Output.CONTROL

        bra .Exit
    +
        lda.w SNES.MUL.PRODUCT_H
        bne +
        // Stop playing track when volume reaches 0.
        stz.w MSU.Output.CONTROL

        cpy.b #MSU.Values.Volume.EMPTY
        bne +
        stz.b Track.CURRENT
    +
        sta.w MSU.Output.VOLUME

    .Exit:
        Register.restore(Register.X|Register.Y|Register.B)

        jmp Default

    .Compute:
        bcc +

        // Fade in
        sbc.b Track.VOLUME
        bra .SetStep
    +
        // Fade out
        sec
        lda.b Track.VOLUME
        sbc.b Track.FADE_VOLUME

    .SetStep:
        sta.w SNES.DIV.DIVIDEND_L
        stz.w SNES.DIV.DIVIDEND_H
        sty.w SNES.DIV.DIVISOR

        // 16 cycles needed for the division results.
        Register.restore(Register.X|Register.Y|Register.B) // 17 cycles.

        lda.l SNES.DIV.QUOTIENT_L
        lsr // Divide original fade step by 2 for MSU-1.
        bne +
        inc // Minimum step of 1.
    +
        sta.b Track.FADE_STEP

        jmp Default
    }

    scope PlayTrack: {
        Register.save(Register.X|Register.Y|Register.B)

        ldx.b SNES.SPC.Game.SOUND_REQUEST
        beq .Stop
        cpx.b #(Tracklist.SIZE - Tracklist.EXTRAS - 1)
        bcs .Exit

        cpx.b #Tracklist.Tracks.THEME
        bne +
        lda.b #Flags.GAME_STARTED
        bit.b FLAGS
        bne +
        // Change attract theme.
        ldx.b #Tracklist.Tracks.THEME_ATTRACT
    +
        cpx.b Track.CURRENT
        bne +
        lda.b #Flags.MSU_AUDIO_STARTED
        bit.b FLAGS
        beq .Exit
        MSU.not_playing(Mode.ABS, .Exit)
    +
        lda.l Tracklist.ADDRESS,x
        beq .Reset
        tay

        stx.w MSU.Output.TRACK_L
        stz.w MSU.Output.TRACK_H

    .Check:
        // Wait until MSU-1 is done loading our track.
        // NOTE: Current implementations for Snes9x, bsnes and sd2snes never set this flag (equivalent to a 6 cycles nop).
        bit.w MSU.Input.STATUS
        bvs .Check

        // Check if track is missing.
        MSU.missing(Mode.ABS, .Play)

    .Reset:
        // Reset track.
        stz.w MSU.Output.TRACK_L
        stz.w MSU.Output.TRACK_H
    -
        bit.w MSU.Input.STATUS
        bvs -

    .Stop:
        // Stop the current track.
        stz.w MSU.Output.CONTROL
        stz.w MSU.Output.VOLUME

        stz.b Track.CURRENT

        lda.b #MSU.Values.Volume.FULL
        sta.b Track.VOLUME
        sta.b Track.FADE_VOLUME

    .Exit:
        Register.restore(Register.X|Register.Y|Register.B)

        jmp Default

    .Play:
        lda.b #Flags.MSU_AUDIO_STARTED
        trb.b FLAGS

        stx.b Track.CURRENT

        // If fading out when new track starts,
        // end fade immediately so we don't end up
        // stopping the new track when we reach 0.
        lda.b Track.FADE_VOLUME
        cmp.b Track.VOLUME
        bcs +
        sta.b Track.VOLUME
    +
        // Is SPC muted?
        lda.b #Flags.SPC_MUTED
        bit.b FLAGS
        beq .Exit

        // Load volume gain for current track.
        lda.b SNES.SPC.Game.SOUND_REQUEST
        asl
        tax
        lda.l $C7241E,x
        sta.b Track.VOLUME_GAIN

        // Play/Resume the track.
        sta.w SNES.MUL.MULTIPLICAND
        lda.b Track.VOLUME
        sta.w SNES.MUL.MULTIPLIER

        // 8 cycles needed for the multiplication results.
        cmp.b #Tracklist.Fade.IN_THRESHOLD // 2 cycles.
        bcc .Exit                          // 2 cycles.

        lda.b #Flags.MSU_AUDIO_STARTED     // 2 cycles.
        tsb.b FLAGS                        // 5 cycles.

        lda.w SNES.MUL.PRODUCT_H
        sta.w MSU.Output.VOLUME

        sty.w MSU.Output.CONTROL

        bra .Exit
    }
}

scope NMI: {
    Register.save(Register.P|Register.A|Register.D)

    lda.b Track.VOLUME
    cmp.b Track.FADE_VOLUME
    beq .Default // Current volume is the same as the fade volume.
    bcc .FadeIn

.FadeOut:
    sbc.b Track.FADE_VOLUME
    cmp.b Track.FADE_STEP
    bcs +
    // Step is bigger than our final volume, just set to fade volume immediately.
    lda.b Track.FADE_VOLUME
    bra ++
+
    lda.b Track.VOLUME
    sbc.b Track.FADE_STEP
+
    sta.b Track.VOLUME

    lda.b Track.CURRENT
    beq .Default

    Register.save(Register.B)

    lda.b Track.VOLUME_GAIN
    sta.w SNES.MUL.MULTIPLICAND
    lda.b Track.VOLUME
    sta.w SNES.MUL.MULTIPLIER

    // 8 cycles needed for the multiplication results.
    bne + // 2/3 cycles.

    stz.w MSU.Output.CONTROL
    stz.w MSU.Output.VOLUME

    stz.b Track.CURRENT

    Register.restore(Register.B)

    bra .Default
+
    xba // 3 cycles.
    nop // 2 cycles.

    lda.w SNES.MUL.PRODUCT_H
    bne +
    // Stop playing track when volume reaches 0.
    stz.w MSU.Output.CONTROL
+
    sta.w MSU.Output.VOLUME

    Register.restore(Register.B)

.Default:
    Register.restore(Register.P|Register.A|Register.D)

    // Original routine
    jml $000500

.FadeIn:
    sec
    lda.b Track.FADE_VOLUME
    sbc.b Track.VOLUME
    cmp.b Track.FADE_STEP
    bcs +
    // Step is bigger than our final volume, just set to fade volume immediately.
    lda.b Track.FADE_VOLUME
    bra ++
+
    clc
    lda.b Track.VOLUME
    adc.b Track.FADE_STEP
+
    sta.b Track.VOLUME

    lda.b Track.CURRENT
    beq .Default

    lda.b #Flags.SPC_MUTED
    bit.b FLAGS
    beq .Default

    Register.save(Register.B)

    lda.b Track.VOLUME_GAIN
    sta.w SNES.MUL.MULTIPLICAND
    lda.b Track.VOLUME
    sta.w SNES.MUL.MULTIPLIER

    // 8 cycles needed for the multiplication results.
    cmp.b #Tracklist.Fade.IN_THRESHOLD // 2 cycles. Sets the c flag.
    lda.b #Flags.MSU_AUDIO_STARTED     // 2 cycles.
    bit.b FLAGS                        // 3 cycles.
    bne +                              // 2/3 cycles.

    bcc ++ // Track volume below threshold.

    // Attempt delayed track load
    tsb.b FLAGS

    Register.save(Register.X|Register.Y)

    lda.w SNES.MUL.PRODUCT_H
    sta.w MSU.Output.VOLUME

    ldx.b Track.CURRENT
    lda.l Tracklist.ADDRESS,x
    sta.w MSU.Output.CONTROL

    Register.restore(Register.X|Register.Y)

    Register.restore(Register.B)

    bra .Default
+
    lda.w SNES.MUL.PRODUCT_H
    sta.w MSU.Output.VOLUME
+
    Register.restore(Register.B)

    bra .Default
}

scope SPCMute: {
    // Original code
    lda.b #$E0
    sta.b $84

    lda.b Track.CURRENT
    bne .Check

    // Is SPC muted?
    lda.b #Flags.SPC_MUTED
    trb.b FLAGS
    bne .Init

.Default:
    return(Hooks.SPC_MUTE, 0)

.Check:
    lda.b #Flags.MSU_AUDIO_STARTED
    bit.b FLAGS
    bne .Default // Skip if the track is already playing.

    // Check to see if SPC is already muted.
    lda.b #Flags.SPC_MUTED
    tsb.b FLAGS
    beq .Init

    lda.l $C7241D,x
    cmp.b $F0
    beq .Default

.Init:
    lda.b #$0A
    sta.w SNES.SPC.COMM3
    lda.b #$4C
    sta.w SNES.SPC.COMM2
    lda.b #$02
    sta.w SNES.SPC.COMM1
    lda.b #$E0
    sta.w SNES.SPC.COMM0
-
    cmp.w SNES.SPC.COMM0
    bne -

    lda.b #$02
    cmp.w SNES.SPC.COMM1
    beq +

    lda.b #$61
    sta.w SNES.SPC.COMM0
-
    cmp.w SNES.SPC.COMM0
    bne -

    bra .Init
+
    ldx.w #$0000

    lda.b Track.CURRENT
    beq .Unmute

.Mute:
    lda.b #$E8
    sta.w SNES.SPC.COMM1
    stz.w SNES.SPC.COMM2
    lda.b #$61
    sta.w SNES.SPC.COMM0
-
    cmp.w SNES.SPC.COMM0
    bne -

    Register.save(Register.X|Register.Y)

    lda.b $02 // Global volume
    sta.b Track.VOLUME_GAIN

    ldx.b Track.VOLUME
    cpx.b #Tracklist.Fade.IN_THRESHOLD
    bcc .Exit

    sta.w SNES.MUL.MULTIPLICAND
    stx.w SNES.MUL.MULTIPLIER

    // 8 cycles needed for the multiplication results.
    lda.b #Flags.MSU_AUDIO_STARTED     // 2 cycles.
    tsb.b FLAGS                        // 5 cycles.

    ldx.b Track.CURRENT                // 3 cycles.
    lda.l Tracklist.ADDRESS,x          // 5 cycles.

    ldy.w SNES.MUL.PRODUCT_H
    sty.w MSU.Output.VOLUME

    sta.w MSU.Output.CONTROL

.Exit:
    Register.restore(Register.X|Register.Y)

    return(Hooks.SPC_MUTE, 0)

.Unmute:
    lda.b #$E4
    sta.w SNES.SPC.COMM1
    lda.b #$4D
    sta.w SNES.SPC.COMM2
    lda.b #$61
    sta.w SNES.SPC.COMM0
-
    cmp.w SNES.SPC.COMM0
    bne -

    return(Hooks.SPC_MUTE, 0)
}

scope SPCEcho: {
    lda.b Track.CURRENT
    beq .Default

    lda.l $C7241D,x
    cmp.b #SNES.SPC.Game.Echo.LIMIT
    bcc .Exit

    lda.b #SNES.SPC.Game.Echo.VALUE

.Exit:
    return(Hooks.SPC_ECHO, 0)

.Default:
    // Original code
    lda.l $C7241D,x

    return(Hooks.SPC_ECHO, 0)
}

scope WaitTrackStart: {
    Memory.load(Mode.LONG, Track.CURRENT, Register.A)
    beq .Default

.MSU:
    rtl
    
.Default:
    // Original code
    lda.l SNES.SPC.COMM3
    and.b #$0F
    beq .Default
    
    rtl
}

scope WaitTrackFinish: {
    Memory.load(Mode.ABS, Track.CURRENT, Register.A)
    beq .Default

.MSU:
    MSU.status(Mode.ABS)
    and.b #MSU.Flags.Status.AUDIO_PLAYING

    return(Hooks.WAIT_TRACK_FINISH, 1)

.Default:
    // Original code
    lda.w SNES.SPC.COMM3
    and.b #$0F

    return(Hooks.WAIT_TRACK_FINISH, 1)
}

scope GameStart: {
    lda.b #Flags.GAME_STARTED
    tsb.w Memory.PAGE | FLAGS

.Default:
    // Original code
    lda.b #$00

    return(Hooks.GAME_START, $14)
}

assert("Patch")
}

// Track list for MSU-1.
// NONE: Ignored.
// STOP: Stop playing current track.
// PLAY: Play track, but only once.
// LOOP: Play track on loop.
scope Tracklist {
seek(ADDRESS)

db Actions.STOP // ($00)
db Actions.LOOP // ($01) 1.05 - Green Memories
db Actions.LOOP // ($02) 1.09 - Yearnings of the Wind
db Actions.LOOP // ($03) 3.04 - Corridor of Time
db Actions.LOOP // ($04) 2.20 - Rhythm of Earth, Wind, and Sky
db Actions.LOOP // ($05) 2.01 - A Desolate World
db Actions.LOOP // ($06) 1.06 - Guardia's Millennial Fair
db Actions.LOOP // ($07) 3.09 - Crono & Marle - A Distant Promise
db Actions.LOOP // ($08) 1.11 - Secret Of The Forest
db Actions.LOOP // ($09) 3.05 - Zeal Palace
db Actions.LOOP // ($0A) 2.10 - Derelict Factory
db Actions.LOOP // ($0B) 2.19 - Ayla's Theme
db Actions.LOOP // ($0C) 1.13 - Guardia Castle - Pride & Glory
db Actions.LOOP // ($0D) 2.05 - Lavos' Theme
db Actions.LOOP // ($0E) 2.09 - Robo's Theme
db Actions.PLAY // ($0F) 1.03 - Morning Glow
db Actions.LOOP // ($10) 1.15 - The Cathedral
db Actions.STOP // ($11)
db Actions.STOP // ($12)
db Actions.LOOP // ($13) 3.10 - The Epoch - Wings of Time
db Actions.LOOP // ($14) 3.06 - Schala's Theme
db Actions.LOOP // ($15) 2.14 - Jolly Ol' Spekkio
db Actions.LOOP // ($16) 1.23 - Critical Moment
db Actions.LOOP // ($17) 1.21 - The Trial
db Actions.LOOP // ($18) 1.02 - The Chrono Trigger Symphony
db Actions.STOP // ($19)
db Actions.STOP // ($1A)
db Actions.LOOP // ($1B) 1.20 - Fanfare 1
db Actions.PLAY // ($1C) 2.12 - Fanfare 2
db Actions.LOOP // ($1D) 3.03 - Depths of the Night
db Actions.LOOP // ($1E) 1.04 - Peaceful Days
db Actions.LOOP // ($1F) 1.08 - Strange Occurences
db Actions.STOP // ($20)
db Actions.STOP // ($21)
db Actions.STOP // ($22)
db Actions.LOOP // ($23) 1.22 - The Hidden Truth
db Actions.PLAY // ($24) 1.16 - A Prayer for the Wayfarer
db Actions.PLAY // ($25) 1.14 - Huh
db Actions.LOOP // ($26) 2.06 - The Last Day of the World
db Actions.LOOP // ($27) 2.07 - Johnny of the Robo Gang
db Actions.LOOP // ($28) 2.24 - Magus Confronted
db Actions.LOOP // ($29) 1.18 - Boss Battle 1
db Actions.LOOP // ($2A) 1.19 - Frog's Theme
db Actions.PLAY // ($2B) 1.10 - Good Night
db Actions.LOOP // ($2C) 2.08 - Bike Chase
db Actions.LOOP // ($2D) 2.04 - Those Without the Will to Live
db Actions.PLAY // ($2E) 2.02 - Mystery from the Past
db Actions.LOOP // ($2F) 2.16 - Creeping through the Sewers
db Actions.PLAY // ($30) 1.01 - A Premonition
db Actions.LOOP // ($31) 3.08 - Ocean Palace
db Actions.LOOP // ($32) 3.14 - The Final Battle
db Actions.LOOP // ($33) 2.03 - Site 16
db Actions.STOP // ($34)
db Actions.STOP // ($35)
db Actions.LOOP // ($36) 2.21 - Burn! Bobonga! Burn!
db Actions.STOP // ($37)
db Actions.LOOP // ($38) 2.18 - Primeval Mountain
db Actions.LOOP // ($39) 3.13 - World Revolution
db Actions.STOP // ($3A)
db Actions.LOOP // ($3B) 3.07 - Sealed Door
db Actions.LOOP // ($3C) 1.17 - Light of Silence
db Actions.PLAY // ($3D) 2.15 - Fanfare 3
db Actions.LOOP // ($3E) 2.13 - At the End of Time
db Actions.PLAY // ($3F) 3.17 - Outskirts of Time
db Actions.LOOP // ($40) 2.23 - Strains of Insanity
db Actions.STOP // ($41)
db Actions.LOOP // ($42) 1.07 - Gato's Song
db Actions.STOP // ($43)
db Actions.LOOP // ($44) 3.11 - Black Omen
db Actions.LOOP // ($45) 1.12 - Battle
db Actions.LOOP // ($46) 3.02 - Tyrano Lair
db Actions.STOP // ($47)
db Actions.PLAY // ($48) 2.22 - The Fiendlord's Keep
db Actions.LOOP // ($49) 3.15 - Festival of Stars
db Actions.STOP // ($4A)
db Actions.STOP // ($4B)
db Actions.STOP // ($4C)
db Actions.LOOP // ($4D) 3.16 - Epilogue - To My Dear Friends
db Actions.LOOP // ($4E) 2.17 - Boss Battle 2
db Actions.STOP // ($4F)
db Actions.LOOP // ($50) 3.12 - Determination
db Actions.LOOP // ($51) 2.11 - Battle 2
db Actions.LOOP // ($52) 3.01 - Singing Mountain
db Actions.NONE // ($53)
db Actions.PLAY // ($54) 1.02 - The Chrono Trigger Symphony

assert("Tracklist")
}
