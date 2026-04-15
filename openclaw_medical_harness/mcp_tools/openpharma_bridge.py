"""OpenPharma MCP Bridge — 50+ biomedical data sources.

This module maps OpenPharma MCP servers to the MedicalToolRegistry,
giving the harness access to 50+ authoritative biomedical databases.

All servers: https://github.com/openpharma-org/
Bundled in: BioClaw (https://github.com/uh-joan/bioclaw)
"""

# OpenPharma server registry
OPENPHARMA_SERVERS = {
    # Drug & Regulatory
    "fda": {
        "name": "FDA",
        "category": "drug",
        "source": "openFDA API",
        "tools": ["drug_label", "adverse_events", "recalls", "shortages"],
        "repo": "https://github.com/openpharma-org/fda-mcp",
    },
    "ema": {
        "name": "EMA",
        "category": "drug",
        "source": "EMA Public JSON API",
        "tools": ["approvals", "epars", "orphan_designations", "shortages"],
        "repo": "https://github.com/openpharma-org/ema-mcp",
    },
    "drugbank": {
        "name": "DrugBank",
        "category": "drug",
        "source": "SQLite (17,430+ drugs)",
        "tools": ["drug_info", "interactions", "targets"],
        "repo": "https://github.com/openpharma-org/drugbank-mcp-server",
    },
    "chembl": {
        "name": "ChEMBL",
        "category": "drug",
        "source": "EMBL-EBI REST API",
        "tools": ["compounds", "targets", "mechanisms", "activities"],
        "repo": "https://github.com/openpharma-org/chembl-mcp",
    },
    "pubchem": {
        "name": "PubChem",
        "category": "drug",
        "source": "PubChem REST API",
        "tools": ["structures", "properties", "compounds"],
        "repo": "https://github.com/openpharma-org/pubchem-mcp",
    },
    "opentargets": {
        "name": "Open Targets",
        "category": "drug",
        "source": "OpenTargets Platform",
        "tools": ["target_validation", "genetic_evidence", "disease_associations"],
        "repo": "https://github.com/openpharma-org/opentargets-mcp",
    },
    "clinicaltrials": {
        "name": "ClinicalTrials.gov",
        "category": "clinical",
        "source": "ClinicalTrials.gov API v2",
        "tools": ["search", "study_details", "outcomes"],
        "repo": "https://github.com/openpharma-org/ct-gov-mcp",
    },
    
    # Genomics
    "ncbi": {
        "name": "NCBI",
        "category": "genomics",
        "source": "NCBI E-utilities",
        "tools": ["gene", "protein", "nucleotide", "omim"],
        "repo": "https://github.com/openpharma-org/ncbi-mcp-server",
    },
    "clinvar": {
        "name": "ClinVar",
        "category": "genomics",
        "source": "ClinVar / NCBI",
        "tools": ["variant_interpretation", "clinical_significance"],
        "repo": "https://github.com/openpharma-org/clinvar-mcp-server",
    },
    "cosmic": {
        "name": "COSMIC",
        "category": "genomics",
        "source": "COSMIC",
        "tools": ["somatic_mutations", "cancer_variants"],
        "repo": "https://github.com/openpharma-org/cosmic-mcp-server",
    },
    "gwas": {
        "name": "GWAS Catalog",
        "category": "genomics",
        "source": "NHGRI-EBI GWAS Catalog",
        "tools": ["associations", "studies"],
        "repo": "https://github.com/openpharma-org/gwas-mcp-server",
    },
    "gnomad": {
        "name": "gnomAD",
        "category": "genomics",
        "source": "gnomAD API",
        "tools": ["allele_frequencies", "population_data"],
        "repo": "https://github.com/openpharma-org/gnomad-mcp-server",
    },
    "ensembl": {
        "name": "Ensembl",
        "category": "genomics",
        "source": "Ensembl REST API",
        "tools": ["genome_annotation", "variation"],
        "repo": "https://github.com/openpharma-org/ensembl-mcp-server",
    },
    "gtex": {
        "name": "GTEx",
        "category": "genomics",
        "source": "GTEx Portal",
        "tools": ["tissue_expression", "gene_expression"],
        "repo": "https://github.com/openpharma-org/gtex-mcp-server",
    },
    "geo": {
        "name": "GEO",
        "category": "genomics",
        "source": "NCBI GEO E-utilities",
        "tools": ["expression_datasets", "series_search"],
        "repo": "https://github.com/openpharma-org/geo-mcp-server",
    },
    "jaspar": {
        "name": "JASPAR",
        "category": "genomics",
        "source": "JASPAR REST API",
        "tools": ["tf_binding_profiles"],
        "repo": "https://github.com/openpharma-org/jaspar-mcp-server",
    },
    
    # Proteomics
    "uniprot": {
        "name": "UniProt",
        "category": "proteomics",
        "source": "UniProt REST API",
        "tools": ["sequences", "functional_annotation", "variants"],
        "repo": "https://github.com/openpharma-org/uniprot-mcp-server",
    },
    "alphafold": {
        "name": "AlphaFold",
        "category": "proteomics",
        "source": "AlphaFold DB API",
        "tools": ["predicted_structures", "confidence_scores"],
        "repo": "https://github.com/openpharma-org/alphafold-mcp-server",
    },
    "pdb": {
        "name": "PDB",
        "category": "proteomics",
        "source": "RCSB PDB REST API",
        "tools": ["experimental_structures", "ligand_info"],
        "repo": "https://github.com/openpharma-org/pdb-mcp-server",
    },
    "stringdb": {
        "name": "STRING-db",
        "category": "proteomics",
        "source": "STRING API",
        "tools": ["protein_interactions", "network_analysis"],
        "repo": "https://github.com/openpharma-org/stringdb-mcp-server",
    },
    "bindingdb": {
        "name": "BindingDB",
        "category": "proteomics",
        "source": "BindingDB",
        "tools": ["binding_affinity", "target_compound_pairs"],
        "repo": "https://github.com/openpharma-org/bindingdb-mcp-server",
    },
    "embl_ebi": {
        "name": "EMBL-EBI",
        "category": "proteomics",
        "source": "EMBL-EBI APIs",
        "tools": ["interpro", "pfam", "protein_features"],
        "repo": "https://github.com/openpharma-org/embl-mcp-server",
    },
    "chebi": {
        "name": "ChEBI",
        "category": "proteomics",
        "source": "ChEBI / OLS4 API",
        "tools": ["chemical_classification", "ontology"],
        "repo": "https://github.com/openpharma-org/chebi-mcp-server",
    },
    
    # Pathways
    "reactome": {
        "name": "Reactome",
        "category": "pathways",
        "source": "Reactome Content Service",
        "tools": ["pathways", "reactions", "interactions"],
        "repo": "https://github.com/openpharma-org/reactome-mcp-server",
    },
    "kegg": {
        "name": "KEGG",
        "category": "pathways",
        "source": "KEGG REST API",
        "tools": ["metabolic_pathways", "signaling_pathways", "diseases"],
        "repo": "https://github.com/openpharma-org/kegg-mcp-server",
    },
    "gene_ontology": {
        "name": "Gene Ontology",
        "category": "pathways",
        "source": "GO API",
        "tools": ["gene_function", "annotations"],
        "repo": "https://github.com/openpharma-org/geneontology-mcp-server",
    },
    "hpo": {
        "name": "HPO",
        "category": "pathways",
        "source": "HPO API",
        "tools": ["phenotype_ontology", "disease_associations"],
        "repo": "https://github.com/openpharma-org/hpo-mcp-server",
    },
    "monarch": {
        "name": "Monarch",
        "category": "pathways",
        "source": "Monarch Initiative API",
        "tools": ["disease_gene_phenotype", "knowledge_graph"],
        "repo": "https://github.com/openpharma-org/monarch-mcp-server",
    },
    
    # Cancer
    "depmap": {
        "name": "DepMap",
        "category": "cancer",
        "source": "DepMap Portal",
        "tools": ["dependencies", "gene_effect", "drug_sensitivity"],
        "repo": "https://github.com/openpharma-org/depmap-mcp-server",
    },
    "cbioportal": {
        "name": "cBioPortal",
        "category": "cancer",
        "source": "cBioPortal API",
        "tools": ["mutations", "expression", "clinical_data"],
        "repo": "https://github.com/openpharma-org/cbioportal-mcp-server",
    },
    
    # Metabolomics & PGx
    "hmdb": {
        "name": "HMDB",
        "category": "metabolomics",
        "source": "Human Metabolome Database",
        "tools": ["metabolites", "disease_associations", "pathways"],
        "repo": "https://github.com/openpharma-org/hmdb-mcp-server",
    },
    "clinpgx": {
        "name": "ClinPGx",
        "category": "pharmacogenomics",
        "source": "PharmGKB",
        "tools": ["drug_gene_interactions", "guidelines", "variants"],
        "repo": "https://github.com/openpharma-org/clinpgx-mcp-server",
    },
    
    # Literature
    "pubmed": {
        "name": "PubMed",
        "category": "literature",
        "source": "PubMed/NCBI E-utilities",
        "tools": ["search", "abstract", "full_text_links"],
        "repo": "https://github.com/openpharma-org/pubmed-mcp",
    },
    "biorxiv": {
        "name": "bioRxiv",
        "category": "literature",
        "source": "bioRxiv/medRxiv API",
        "tools": ["preprint_search", "tracking"],
        "repo": "https://github.com/openpharma-org/biorxiv-mcp",
    },
    "openalex": {
        "name": "OpenAlex",
        "category": "literature",
        "source": "OpenAlex API",
        "tools": ["scholarly_works", "citations", "authors", "institutions"],
        "repo": "https://github.com/openpharma-org/openalex-mcp-server",
    },
    "crossref": {
        "name": "CrossRef",
        "category": "literature",
        "source": "CrossRef REST API",
        "tools": ["doi_metadata", "citations", "150M+_works"],
        "repo": "https://github.com/openpharma-org/crossref-mcp-server",
    },
    "core": {
        "name": "CORE",
        "category": "literature",
        "source": "CORE API v3",
        "tools": ["open_access_papers", "full_text"],
        "repo": "https://github.com/openpharma-org/core-mcp-server",
    },
    
    # Clinical & Health Systems
    "nlm_codes": {
        "name": "NLM Codes",
        "category": "clinical",
        "source": "NLM Clinical Tables API",
        "tools": ["icd10", "icd11", "hcpcs", "npi"],
        "repo": "https://github.com/openpharma-org/nlm-codes-mcp",
    },
    "cdc": {
        "name": "CDC",
        "category": "clinical",
        "source": "CDC WONDER, Socrata APIs",
        "tools": ["disease_surveillance", "vaccination_data"],
        "repo": "https://github.com/openpharma-org/cdc-mcp",
    },
    "medicare": {
        "name": "Medicare",
        "category": "clinical",
        "source": "CMS Medicare API",
        "tools": ["claims", "provider_data"],
        "repo": "https://github.com/openpharma-org/medicare-mcp",
    },
    "medicaid": {
        "name": "Medicaid",
        "category": "clinical",
        "source": "CMS DKAN",
        "tools": ["formularies", "drug_pricing", "enrollment"],
        "repo": "https://github.com/openpharma-org/medicaid-mcp-server",
    },
}


def get_servers_by_category(category: str) -> dict:
    """Get all OpenPharma servers in a category."""
    return {k: v for k, v in OPENPHARMA_SERVERS.items() if v["category"] == category}


def get_categories() -> list:
    """Get all available categories."""
    return list(set(v["category"] for v in OPENPHARMA_SERVERS.values()))


def get_all_tools() -> list:
    """Get all available tools across all servers."""
    tools = []
    for server_id, server in OPENPHARMA_SERVERS.items():
        for tool in server["tools"]:
            tools.append({
                "server": server_id,
                "tool": tool,
                "category": server["category"],
                "source": server["source"],
            })
    return tools


def get_server_info(server_id: str) -> dict:
    """Get info for a specific server."""
    return OPENPHARMA_SERVERS.get(server_id, {})
