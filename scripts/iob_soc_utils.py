import os

#
# Functions for iob_soc.py
#


def update_params(params, py_params):
    """Update given `params` dictionary with values from `py_params` dictionary.
    Paramters will be updated to have the same type as the default value.
    :param dict params: dictionary to update. Contains default values and their types.
    :param dict py_params: dictionary to use as source. Contains new values.
                           Their types will be converted to match the corresponding default type.
    """
    for name, default_val in params.items():
        if name not in py_params:
            continue
        if type(default_val) is bool and py_params[name] == "0":
            params[name] = False
        else:
            params[name] = type(default_val)(py_params[name])


def iob_soc_scripts(attributes_dict, params, py_params):
    """IOb-SoC automatic setup scripts.
    :param dict attributes_dict: iob_soc attributes
    :param dict params: iob_soc python parameters
    :param dict py_params: iob_soc argument python parameters
    """
    set_build_dir(attributes_dict, py_params)
    peripherals = get_iob_soc_peripherals_list(attributes_dict)
    connect_peripherals_cbus(attributes_dict, peripherals, params)
    generate_makefile_segments(attributes_dict, peripherals, params, py_params)
    generate_peripheral_base_addresses(attributes_dict, peripherals, params, py_params)


#
# Local functions
#


def set_build_dir(attributes_dict, py_params):
    """If build_dir not given in py_params, set a default one.
    :param dict attributes_dict: iob_soc attributes
    :param dict py_params: iob_soc argument python parameters
    """
    if "build_dir" in py_params and py_params["build_dir"]:
        build_dir = py_params["build_dir"]
    else:
        build_dir = f"../{attributes_dict['name']}_V{attributes_dict['version']}"
    attributes_dict["build_dir"] = build_dir


def get_iob_soc_peripherals_list(attributes_dict):
    """Parses blocks list in iob_soc attributes, for blocks with the `is_peripheral` attribute set to True.
    Also removes `is_peripheral` attribute from each block after adding it to the peripherals list.
    """
    peripherals = []
    for block in attributes_dict["blocks"]:
        if "is_peripheral" in block and block["is_peripheral"]:
            peripherals.append(block)
            block.pop("is_peripheral")
    return peripherals


def connect_peripherals_cbus(attributes_dict, peripherals, params):
    """Update given attributes_dict to connect peripherals cbus to system's pbus_split.
    :param dict attributes_dict: iob_soc attributes
    :param list peripherals: list of peripheral blocks
    :param dict params: iob_soc python parameters
    """
    # Find pbus_split
    pbus_split = None
    for block in attributes_dict["blocks"]:
        if block["instance_name"] == "iob_axil_pbus_split":
            pbus_split = block

    # Number of peripherals = peripherals + CLINT + PLIC
    num_peripherals = len(peripherals) + 2
    peripheral_addr_w = params["addr_w"] - 1 - (num_peripherals - 1).bit_length()

    # Configure number of connections to pbus_split
    pbus_split["num_outputs"] = num_peripherals

    for idx, peripheral in enumerate(peripherals):
        peripheral_name = peripheral["instance_name"].lower()
        # Add peripheral cbus wire
        attributes_dict["wires"].append(
            {
                "name": f"{peripheral_name}_cbus",
                "descr": f"{peripheral_name} Control/Status Registers bus",
                "interface": {
                    "type": "axil",
                    "wire_prefix": f"{peripheral_name}_cbus_",
                    "ID_W": "AXI_ID_W",
                    "ADDR_W": peripheral_addr_w,
                    "DATA_W": "AXI_DATA_W",
                    "LEN_W": "AXI_LEN_W",
                },
            },
        )
        # Connect cbus to pbus_split
        pbus_split["connect"][f"output_{idx}"] = f"{peripheral_name}_cbus"
        # Connect cbus to peripheral
        peripheral["connect"]["cbus"] = f"{peripheral_name}_cbus"

    # Add CLINT and PLIC wires (they are not in peripherals list)
    attributes_dict["wires"] += [
        {
            "name": "clint_cbus",
            "descr": "CLINT Control/Status Registers bus",
            "interface": {
                "type": "axil",
                "wire_prefix": "clint_cbus_",
                "ID_W": "AXI_ID_W",
                "ADDR_W": peripheral_addr_w,
                "DATA_W": "AXI_DATA_W",
                "LEN_W": "AXI_LEN_W",
            },
        },
        {
            "name": "plic_cbus",
            "descr": "PLIC Control/Status Registers bus",
            "interface": {
                "type": "axil",
                "wire_prefix": "plic_cbus_",
                "ID_W": "AXI_ID_W",
                "ADDR_W": peripheral_addr_w,
                "DATA_W": "AXI_DATA_W",
                "LEN_W": "AXI_LEN_W",
            },
        },
    ]

    # Connect CLINT and PLIC cbus to last outputs of pbus_split
    pbus_split["connect"][f"output_{num_peripherals-2}"] = "clint_cbus"
    pbus_split["connect"][f"output_{num_peripherals-1}"] = "plic_cbus"


def generate_peripheral_base_addresses(
    attributes_dict, peripherals_list, params, py_params
):
    """Create C header file containing peripheral base addresses.
    :param dict attributes_dict: iob_soc attributes
    :param list peripherals_list: list of peripheral blocks
    :param dict params: iob_soc python parameters
    :param dict py_params: iob_soc argument python parameters
    """
    out_file = os.path.join(
        attributes_dict["build_dir"], "software", f"{attributes_dict['name']}_periphs.h"
    )
    # Don't override output file
    if os.path.isfile(out_file):
        return

    # Include CLINT and PLIC in peripherals list
    complete_peripherals_list = peripherals_list + [
        {"instance_name": "CLINT0"},
        {"instance_name": "PLIC0"},
    ]
    n_slaves_w = (len(complete_peripherals_list) - 1).bit_length()

    # Don't create files for other targets (like clean)
    if "py2hwsw_target" not in py_params or py_params["py2hwsw_target"] != "setup":
        return

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        for idx, instance in enumerate(complete_peripherals_list):
            instance_name = instance["instance_name"]
            f.write(
                f"#define {instance_name}_BASE (PBUS_BASE + ({idx}<<(P_BIT-{n_slaves_w})))\n"
            )


def generate_makefile_segments(attributes_dict, peripherals, params, py_params):
    """Generate automatic makefile segments for iob_soc.
    :param dict attributes_dict: iob_soc attributes
    :param list peripherals: list of peripheral blocks
    :param dict params: iob_soc python parameters
    :param dict py_params: iob_soc argument python parameters
    """
    build_dir = attributes_dict["build_dir"]

    # Don't create files for other targets (like clean)
    if "py2hwsw_target" not in py_params or py_params["py2hwsw_target"] != "setup":
        return

    #
    # Create auto_sw_build.mk
    #
    os.makedirs(f"{build_dir}/software", exist_ok=True)
    with open(f"{build_dir}/software/auto_sw_build.mk", "w") as file:
        file.write("#This file was auto generated by iob_soc_utils.py\n")
        # Create a list with every peripheral name, except clint, and plic
        file.write(
            "PERIPHERALS ?="
            + " ".join(peripheral["core_name"] for peripheral in peripherals)
            + "\n",
        )
        if params["use_ethernet"]:
            # Set custom ethernet CONSOLE_CMD
            file.write(
                'CONSOLE_CMD ?=rm -f soc2cnsl cnsl2soc; $(IOB_CONSOLE_PYTHON_ENV) $(PYTHON_DIR)/console_ethernet.py -L -c $(PYTHON_DIR)/console.py -m "$(RMAC_ADDR)" -i "$(ETH_IF)"\n',
            )
            file.write(
                """\
    UTARGETS+=iob_eth_rmac.h
    EMUL_HDR+=iob_eth_rmac.h
    iob_eth_rmac.h:
        echo "#define ETH_RMAC_ADDR 0x$(RMAC_ADDR)" > $@\n
""",
            )

    #
    # Create auto_fpga_build.mk
    #
    os.makedirs(f"{build_dir}/hardware/fpga", exist_ok=True)
    with open(f"{build_dir}/hardware/fpga/auto_fpga_build.mk", "w") as file:
        file.write("#This file was auto generated by iob_soc_utils.py\n")

        # Set N_INTERCONNECT_SLAVES variable
        # TODO: Count axi interfaces automatically for peripherals with DMA
        file.write("N_INTERCONNECT_SLAVES:=1\n")
        # Set USE_EXTMEM variable
        file.write(f"USE_EXTMEM:={int(params['use_extmem'])}\n")
        # Set INIT_MEM variable
        file.write(f"INIT_MEM:={int(params['init_mem'])}\n")
        if params["use_ethernet"]:
            # Set custom ethernet CONSOLE_CMD
            file.write(
                'CONSOLE_CMD=$(IOB_CONSOLE_PYTHON_ENV) $(PYTHON_DIR)/console_ethernet.py -s /dev/usb-uart -c $(PYTHON_DIR)/console.py -m "$(RMAC_ADDR)" -i "$(ETH_IF)"\n',
            )

    #
    # Create auto_sim_build.mk
    #
    os.makedirs(f"{build_dir}/hardware/simulation", exist_ok=True)
    with open(f"{build_dir}/hardware/simulation/auto_sim_build.mk", "w") as file:
        file.write("#This file was auto generated by iob_soc_utils.py\n")
        if params["use_ethernet"]:
            file.write("USE_ETHERNET=1\n")
            # Set custom ethernet CONSOLE_CMD
            file.write(
                'ETH2FILE_SCRIPT="$(PYTHON_DIR)/eth2file.py"\n'
                'CONSOLE_CMD=$(IOB_CONSOLE_PYTHON_ENV) $(PYTHON_DIR)/console_ethernet.py -L -c $(PYTHON_DIR)/console.py -e $(ETH2FILE_SCRIPT) -m "$(RMAC_ADDR)" -i "$(ETH_IF)" -t 60\n',
            )

    #
    # Create auto_iob_soc_boot.lds and auto_iob_soc_firmware.lds
    #
    os.makedirs(f"{build_dir}/software", exist_ok=True)
    with open(f"{build_dir}/software/auto_iob_soc_boot.lds", "w") as file:
        file.write("/* This file was auto generated by iob_soc_utils.py */\n")
        file.write(
            f". = {hex((1 << params['mem_addr_w']) - (1 << params['bootrom_addr_w']))};\n"
        )
    with open(f"{build_dir}/software/auto_iob_soc_firmware.lds", "w") as file:
        file.write("/* This file was auto generated by iob_soc_utils.py */\n")
        file.write(f". = {params['fw_addr']};\n")
