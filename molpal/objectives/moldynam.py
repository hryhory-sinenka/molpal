import subprocess
from pathlib import Path
from timeit import default_timer as time
from typing import Dict, Iterable, Optional

from configargparse import ArgumentParser

from molpal.objectives.base import Objective
from molpal.objectives.utils import init_realtime_console


class MoldynamObjective(Objective):

    def __init__(self, objective_config: str, minimize: bool = True, **kwargs):
        super().__init__(minimize=minimize)
        path = parse_config(objective_config)
        self.path = Path(path)

        self.master_script = self.path / "master_script.sh"
        if not self.master_script.exists():
            raise FileNotFoundError(f"Master script not found at {self.master_script}")

        self.smi_dict = parse_smis(self.path)
        print(f"Found {len(self.smi_dict)} molecules in gromacs folder")

    def forward(self, smis: Iterable[str], *args, **kwargs) -> Dict[str, Optional[float]]:
        """Calculate the scores for a list of SMILES strings by gromacs calculation

        Parameters
        ----------
        smis : List[str]
            the SMILES strings of the molecules to calculate scores
        **kwargs
            additional and unused positional and keyword arguments

        Returns
        -------
        scores : Dict[str, Optional[float]]
            a map from SMILES string to score. Ligands that failed
            to calculate will be scored as None
        """
        iter = kwargs.get("iter", 0)
        output_dir = kwargs.get("output_dir", ".")
        folders = [self.smi_dict[smi] for smi in smis]
        txt_path = self.path / "folders_cycle.txt"
        with open(txt_path, "w") as f:
            for folder in folders:
                f.write(f"{folder}\n")

        cmd = ["bash", str(self.master_script), str(txt_path)]
        log_path = f"{output_dir}/logs/gromacs_{iter}.log"
        print(f"Running moldynam for {len(smis)} molecules")
        print(f"Log path: {log_path}")

        init_realtime_console(cmd, log_path)

        print(f"End of gromacs calculation")

        result = {}
        for smi, folder in zip(smis, folders):
            score_path = folder / "avg_rmsd.txt"
            try:
                with open(score_path, "r") as f:
                    score = f.read()
                result[smi] = self.c * float(score)
            except Exception as e:
                print(f"Error reading avg_rmsd.txt in {folder}: {e}")
                result[smi] = None
        return result



def parse_config(config: str):
    """parse a LookupObjective configuration file

    Parameters
    ----------
    config : str
        the config file to parse

    Returns
    -------
    path : str
        path where lygand folders and master bash script are located

    """
    parser = ArgumentParser()
    parser.add_argument("config", is_config_file=True)
    parser.add_argument("--path", required=True)

    args = parser.parse_args(config)
    return args.path


def parse_smis(molecules_path: Path):
    folders = list(molecules_path.glob("*_pose_*"))
    smi_dict = {}
    for folder in folders:
        smi_path = folder / "ligand.smi"
        if smi_path.exists():
            with open(smi_path, "r") as f:
                smi_lines = f.read()
            smi_dict[smi_lines.split()[0]] = folder
        else:
            print(f"Ligand.smi not found in {folder}")
    return smi_dict


# def main():
# path = "/home/gsinenko/molpal/examples/mol_obj.ini"
# moldynam_objective = MoldynamObjective(path)

# smis = ["Brc1ccc2c(c1)CN(C(=O)N2)C", "CCOc1cc(cc(c1)c1c(C)noc1C)[C@H](O)C"]
# result = moldynam_objective.forward(smis)
# print(result)


# if __name__ == "__main__":
#     main()
