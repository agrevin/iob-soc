import sys

from iob_core import iob_core


class iob_ram_dp_be_xil(iob_core):
    def __init__(self, *args, **kwargs):
        self.set_default_attribute("version", "0.1")
        self.set_default_attribute("generate_hw", False)
        super().__init__(*args, **kwargs)


if __name__ == "__main__":
    if "clean" in sys.argv:
        iob_ram_dp_be_xil.clean_build_dir()
    elif "print" in sys.argv:
        iob_ram_dp_be_xil.print_build_dir()
    else:
        iob_ram_dp_be_xil()
