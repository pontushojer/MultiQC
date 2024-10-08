import csv
import logging

from multiqc.base_module import BaseMultiqcModule, ModuleNoSamplesFound
from multiqc.plots import table

log = logging.getLogger(__name__)


class MultiqcModule(BaseMultiqcModule):
    def __init__(self):
        super(MultiqcModule, self).__init__(
            name="Nextclade",
            anchor="nextclade",
            href="https://github.com/nextstrain/nextclade",
            info="Viral genome alignment, clade assignment, mutation calling, and quality checks",
            extra="""
            Nextclade assigns input sequences to SARS-Cov-2 clades based on differences between the input sequences 
            and [Nextstrain](https://nextstrain.org/) reference sequences. In addition, it judges the validity of 
            the samples by performing several quality control checks on the input sequences.
            """,
            doi="10.21105/joss.03773",
        )

        # Parse logs
        self.nextclade_data = dict()
        for f in self.find_log_files("nextclade", filehandles=True):
            self.parse_nextclade_log(f)
            self.add_data_source(f)

        # Remove ignored samples
        self.nextclade_data = self.ignore_samples(self.nextclade_data)

        # Check if we found any samples
        if len(self.nextclade_data) == 0:
            raise ModuleNoSamplesFound

        log.info(f"Found {len(self.nextclade_data)} samples")

        # Superfluous function call to confirm that it is used in this module
        # Replace None with actual version if it is available
        self.add_software_version(None)

        self.write_data_file(self.nextclade_data, "multiqc_nextclade")

        # Add data to general statistics table
        self.nextclade_general_stats_table()

        # Create the Nextclade table
        self.add_section(
            name="Run table", anchor="nextclade-run", description="", helptext="", plot=self.nextclade_table()
        )

    def parse_nextclade_log(self, f):
        for sample in csv.DictReader(f["f"], delimiter=";"):
            try:
                s_name = sample.pop("seqName")
                s_name = self.clean_s_name(s_name, f)
                if s_name in self.nextclade_data:
                    log.error(f"Found duplicate sample '{s_name}' - overwriting")

                # Clean column names: make lower case and
                # replace '.' with '_'
                for key in list(sample.keys()):
                    new_key = key.lower()
                    if "." in new_key:
                        new_key = "_".join(new_key.split("."))
                    sample[new_key] = sample.pop(key)

                for key in list(sample.keys()):
                    new_key = key.lower()
                    sample[new_key] = sample.pop(key)
                    try:
                        sample[new_key] = float(sample[new_key])
                    except ValueError:
                        pass

                self.nextclade_data[s_name] = sample
            except KeyError:
                log.error(f"File '{f['fn']}' could not be parsed - no sequence name found")

    def nextclade_general_stats_table(self):
        """Takes the parsed sample data and adds the sequences' clade to the general stats table"""

        headers = {
            "clade": {
                "title": "Clade",
                "description": "Clade",
                "scale": False,
            }
        }
        self.general_stats_addcols(self.nextclade_data, headers)

    def nextclade_table(self):
        """Creates the table of data for the samples"""

        headers = {
            "clade": {
                "title": "Clade",
                "description": "The inferred clade from the input sequence and reference tree",
                "scale": False,
            },
            "qc_overallscore": {
                "title": "Overall score",
                "description": "Summarizing score of all QC test",
                "hidden": True,
            },
            "qc_overallstatus": {
                "title": "Overall status",
                "description": "Summarizing status of all QC tests",
                "scale": False,
                "cond_formatting_rules": {
                    "pass": [{"s_eq": "good"}],
                    "fail": [{"s_eq": "bad"}],
                },
            },
            "totalgaps": {
                "title": "Gaps",
                "description": "Total number of detected nucleotide gaps",
                "min": 0,
                "scale": "RdBu-rev",
                "hidden": True,
            },
            "totalinsertions": {
                "title": "Insertions",
                "description": "Total number of detected nucleotide insertions",
                "min": 0,
                "scale": "RdYlGn-rev",
                "hidden": True,
            },
            "totalmissing": {
                "title": "Missing",
                "description": "Total number of detected missing nucleotides",
                "min": 0,
                "scale": "RdYlBu-rev",
                "hidden": True,
            },
            "totalmutations": {
                "title": "Mutations",
                "description": "Total number of detected nucleotide mutations",
                "min": 0,
                "scale": "RdBu-rev",
                "hidden": True,
            },
            "totalnonacgtns": {
                "title": "Non-ACGTNs",
                "description": "Total number of detected ambiguous nucleotides",
                "min": 0,
                "scale": "RdYlGn-rev",
                "hidden": True,
            },
            "totalpcrprimerchanges": {
                "title": "PCR primer changes",
                "description": "Total number of nucleotide mutations detected in PCR primer regions",
                "min": 0,
                "scale": "RdYlBu-rev",
                "hidden": True,
            },
            "totalaminoacidsubstitutions": {
                "title": "Substitutions",
                "description": "Total number of detected aminoacid substitutions",
                "min": 0,
                "scale": "RdBu-rev",
                "hidden": True,
            },
            "totalaminoaciddeletions": {
                "title": "Deletions",
                "description": "Total number of detected aminoacid substitutions",
                "min": 0,
                "scale": "RdYlGn-rev",
                "hidden": True,
            },
            "alignmentscore": {
                "title": "Alignment score",
                "description": "Indicates to what degree the input sequence and the reference sequence correspond",
                "min": 0,
                "scale": "RdYlBu-rev",
                "hidden": True,
            },
            "alignmentstart": {
                "title": "Alignment start",
                "description": "Beginning of the sequenced region",
                "hidden": True,
            },
            "alignmentend": {
                "title": "Alignment end",
                "description": "End of the sequenced region",
                "hidden": True,
            },
            "qc_missingdata_missingdatathreshold": {
                "title": "Missing data threshold",
                "description": "The threshold used for the 'Missing data' QC test",
                "scale": "GnBu",
                "hidden": True,
            },
            "qc_missingdata_score": {
                "title": "Missing data score",
                "description": "Score from the 'Missing data' QC test",
                "scale": "RdYlGn-rev",
                "hidden": True,
            },
            "qc_missingdata_status": {
                "title": "Missing data status",
                "description": "Status for 'Missing data' QC test",
                "scale": False,
                "cond_formatting_rules": {
                    "pass": [{"s_eq": "good"}],
                    "fail": [{"s_eq": "bad"}],
                },
            },
            "qc_missingdata_totalmissing": {
                "title": "Missing data total",
                "description": "Total number of missing nucleotides used in 'Missing data' QC test",
                "scale": "RdYlBu-rev",
                "hidden": True,
            },
            "qc_mixedsites_mixedsitesthreshold": {
                "title": "Mixed sites threshold",
                "description": "Threshold used for 'Mixed sites' QC test",
                "scale": "GnBu",
                "hidden": True,
            },
            "qc_mixedsites_score": {
                "title": "Mixed sites score",
                "description": "Score from the 'Missing data' QC testScore from the 'Missing data' QC test",
                "scale": "RdYlGn-rev",
                "hidden": True,
            },
            "qc_mixedsites_status": {
                "title": "Mixed sites status",
                "description": "Status for 'Missing data' QC test",
                "scale": False,
                "cond_formatting_rules": {
                    "pass": [{"s_eq": "good"}],
                    "fail": [{"s_eq": "bad"}],
                },
            },
            "qc_mixedsites_totalmixedsites": {
                "title": "Mixed sites total",
                "description": "Total number of ambiguous nucleotides used for 'Mixed sites' QC test",
                "scale": "RdYlBu-rev",
                "hidden": True,
            },
            "qc_privatemutations_cutoff": {
                "title": "Private mutations cutoff",
                "description": "Cutoff parameter used for 'Private mutations' QC test",
                "scale": "GnBu",
                "hidden": True,
            },
            "qc_privatemutations_excess": {
                "title": "Private mutations excess",
                "description": "Excess parameter used for 'Private mutations' QC test",
                "scale": "OrRd",
                "hidden": True,
            },
            "qc_privatemutations_score": {
                "title": "Private mutations score",
                "description": "Score for 'Private mutations' QC rule",
                "scale": "RdYlGn-rev",
                "hidden": True,
            },
            "qc_privatemutations_status": {
                "title": "Private mutations status",
                "description": "Status for 'Private mutations' QC rule",
                "scale": False,
                "cond_formatting_rules": {
                    "pass": [{"s_eq": "good"}],
                    "fail": [{"s_eq": "bad"}],
                },
                "hidden": True,
            },
            "qc_privatemutations_total": {
                "title": "Private mutations",
                "description": "Total number of private mutations used for 'Private mutations' QC rule",
                "scale": "RdYlBu-rev",
                "hidden": True,
            },
            "qc_snpclusters_clusteredsnps": {
                "title": "Clustered SNPs",
                "description": "Clustered SNP detected for 'SNP clusters' QC test",
                "hidden": True,
            },
            "qc_snpclusters_score": {
                "title": "SNP clusters score",
                "description": "Score for 'SNP clusters' QC test",
                "scale": "RdYlGn-rev",
                "hidden": True,
            },
            "qc_snpclusters_status": {
                "title": "SNP clusters status",
                "description": "Status for 'SNP clusters' QC test",
                "scale": False,
                "cond_formatting_rules": {
                    "pass": [{"s_eq": "good"}],
                    "fail": [{"s_eq": "bad"}],
                },
                "hidden": True,
            },
            "qc_snpclusters_totalsnps": {
                "title": "SNPs",
                "description": "Total number of SNPs for 'SNP clusters' QC test",
                "scale": "RdYlBu-rev",
                "hidden": True,
            },
        }

        # Main table config
        table_config = {
            "namespace": "Nextclade",
            "id": "nextclade_run_table",
            "title": "Nextclade Run details",
        }

        return table.plot(self.nextclade_data, headers, table_config)
