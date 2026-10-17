# Assembling and programming the GALs

Three ATF22V10C (or GAL22V10) chips: `ide`, `iobase`, `busctl`. Ready-made JEDEC files are in [`../gal`](../gal).

## Assemble on Linux (e.g. Linux Mint)

```sh
sudo apt install build-essential git
git clone https://github.com/daveho/GALasm
make -C GALasm/src
GALasm/src/galasm gal/ide.pld      # creates ide.jed, ide.pin, ide.chp, ide.fus
```

Check the equations against the intended address map:

```sh
python3 tests/check_gal.py
```

## Program

- XGecu T48 / TL866II+: Xgpro software (Windows), device `ATF22V10C`, load the `.jed` file, program and verify.
- Linux: [minipro](https://gitlab.com/DavidGriffith/minipro) supports the TL866II+; T48 support is still marked experimental there – check before relying on it.
- Leave the security fuse off so the chips can be read back.
