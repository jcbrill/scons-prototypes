import argparse
import json
import os

class Results:

    _vs_version_map = {
        "17": "VS2022",
        "16": "VS2019",
        "15": "VS2017",
        "14": "VS2015",
        "12": "VS2013",
        "11": "VS2012",
        "10": "VS2010",
        "9": "VS2008",
        "8": "VS2005",
        "7.1": "VS2003",
        "7.0": "VS2002",
        "6": "VC6",
    }

    @classmethod
    def _vs_symbol(cls, vs_version):
        vs_comps = vs_version.split(".")
        for key in [
            vs_comps[0],
            ".".join([vs_comps[0], vs_comps[1][0]])
        ]:
            name = cls._vs_version_map.get(key)
            if name:
                return name
        raise RuntimeError()

    @classmethod
    def json_file(cls, filename):
        with open(filename, "r") as fh:
            json_data = json.load(fh)
        return json_data

    @classmethod
    def load_json_data(cls, prefix="../results", bits_filter=None, host_filter=None):
        results = {}
        for key, filename, bits, host in [
            ("AMD64", "_results_PC-AMD64.json", 64, "PC"),
            ("ARM64", "_results_PC-ARM64.json", 64, "PC"),
            ("DEV-64", "_results_VS64-DEV-W11.json", 64, "VM"),
            ("DEV-32", "_results_VS32-DEV-W10.json", 32, "VM"),
            ("BT-64", "_results_VS64-BT-W11.json", 64, "VM"),
            ("BT-32", "_results_VS32-BT-W10.json", 32, "VM"),
            ("EXP-64", "_results_VS64-EXP-W11.json", 64, "VM"),
            ("EXP-32", "_results_VS32-EXP-W10.json", 32, "VM"),
        ]:
            if bits_filter and bits not in bits_filter:
                continue
            if host_filter and host not in host_filter:
                continue
            if prefix:
                filename = os.path.join(prefix, filename)
            results[key] = cls.json_file(filename)
        return results

    @classmethod
    def generate_table(cls, results):
        record = "|Host|VS|VS Version|VC Toolset|CL Version|MSBuild Version|"
        print(record)
        record = "|:-|:-|:-|:-|:-|:-|"
        print(record)
        for key, json_data in results.items():
            for instance in json_data:
                version_info = instance['version_info']
                vs_version = version_info['VS_VERSION']
                vc_toolset = version_info['VC_TOOLSET']
                vc_buildtools = version_info['VC_BUILDTOOLS']
                cl_version = version_info['CL_VERSION']
                mb_version = version_info['MSBUILD_VERSION']
                vs_name = cls._vs_symbol(vs_version)
                record = f"|{key}|{vs_name}|{vs_version}|{vc_toolset}|{cl_version}|{mb_version}|"
                print(record)

    _filter_map = {
        "all-all": {"bits_filter": [32, 64], "host_filter": ["PC", "VM"]},
        "64-all": {"bits_filter": [64], "host_filter": ["PC", "VM"]},
        "32-all": {"bits_filter": [32], "host_filter": ["PC", "VM"]},
        "all-pc": {"bits_filter": [32, 64], "host_filter": ["PC"]},
        "all-vm": {"bits_filter": [32, 64], "host_filter": ["VM"]},
        "64-pc": {"bits_filter": [64], "host_filter": ["PC"]},
        "64-vm": {"bits_filter": [64], "host_filter": ["VM"]},
        "32-pc": {"bits_filter": [32], "host_filter": ["PC"]},
        "32-vm": {"bits_filter": [32], "host_filter": ["VM"]},
    }

    @classmethod
    def main(cls, bits=None, host=None):
        if bits is None:
            bits = "all"
        if host is None:
            host = "all"
        key = f"{bits.lower()}-{host.lower()}"
        filters = cls._filter_map[key]
        results = cls.load_json_data(**filters)
        cls.generate_table(results)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bits", help="host os bits: 32, 64, ALL", default="ALL")
    parser.add_argument("--host", help="host: PC, VM, ALL", default="ALL")
    args = parser.parse_args()
    bits = args.bits
    host = args.host
    Results.main(bits=bits, host=host)

