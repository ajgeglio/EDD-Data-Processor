def assign_matrix(sample_id):
    sample_str = str(sample_id).strip()
    
    # 1. Groundwater wells starting with MW- and P-
    if sample_str.startswith('MW-'): 
        return 'WG'
    elif sample_str.startswith('P-'):
        return 'WG'
    elif sample_str.startswith('SW'):
        return 'WS'
    elif sample_str.startswith('PW-'):
        return 'WG'
    elif sample_str.startswith('P'):
        return 'WG'
    # 2. Specific site locations
    elif sample_str == 'Leachate':
        return 'LE'
    elif sample_str in ['GROESBECK POND', 'COOPER-1', 'COOPER-2', 'UNDERDRAIN']:
        return 'WS'
    elif sample_str in ['RECYCLING WELL', 'ELECTRIC WELL']:
        return 'WG'
    # 3. QA/QC Samples
    elif 'Duplicate' in sample_str:
        return 'WG'  # Field duplicates inherit parent matrix
    elif 'DupA' in sample_str:
        return 'WG'  # Field duplicates inherit parent matrix
    elif 'DupB' in sample_str:
        return 'WG'  # Field duplicates inherit parent matrix
    elif 'DupC' in sample_str:
        return 'WG'  # Field duplicates inherit parent matrix
    elif 'Blank' in sample_str:
        return 'WQ'  # Trip, Equipment, and Field blanks stay WQ
    
    else:
        return 'U' # Unknown/Unassigned

edd_to_template_mapping = {
    'Lab_ID': 'lab_sample_id',
    'Sample_ID': 'sys_loc_code',                 # Can also map to 'sample_name'
    'Analyte': 'chemical_name',                       # Usually contains modifiers like '<' or 'ND'; often used to populate 'detect_flag'
    'Result': 'result_value',                         # Maps to 'result_value' (reported text/numeric result)   # If 'Result' holds the text/ND value, 'Concentration' may hold the raw numeric value
    'Results': 'result_value',                         # Maps to 'result_value' (reported text/numeric result)   # If 'Result' holds the text/ND value, 'Concentration' may hold the raw numeric value
    'Comment': 'lab_qualifiers',                     # Can also map to 'sample_comments' depending on context
    'Comment': 'result_comments',                     # Can also map to 'sample_comments' depending on context
    'Units': 'result_unit',
    'Matrix': 'lab_matrix',                   # Can also map to 'lab_matrix'
    'Sample_Collection_Date': 'sample_date',          # Time component may need to be parsed into 'sample_time'                # No received date field exists in this template list
    'Date_Extracted': 'prep_date',                    # Time component may need to be parsed into 'prep_time'
    'Date_Analyzed': 'analysis_date',                 # Time component may need to be parsed into 'analysis_time'
    'Detection_Limits': 'method_detection_limit',
    'DETECTION_LIMITS': 'method_detection_limit',
    'Reporting_Limits': 'reporting_detection_limit',
    'Dilution_Factor': 'dilution_factor',
    'DILUTION' : 'dilution_factor',
    'CAS Number': 'cas_rn',
    'Extraction_Method': 'prep_method',
    'Sample_Fraction': 'fraction',
    'Analytical_Method_Reference': 'analytic_method',              # Usually redundant with description; both can map to 'analytic_method'
    'Laboratory_QC_Level': 'validation_level',        # Can also map to 'test_type' or 'workflow_status' depending on lab data
    'Project_Name': 'task_code',                      # Can also map to 'task_type' if 'task_code' is numeric
    'Project_Number': 'LAB_PROJ_NUMBER'
}

sample_id_dict = {
    "Under Drain": "UNDERDRAIN",
    'Underdrain': 'UNDERDRAIN',
    "Leachate": "LEACHATE",
    'Groesbeck Pond': 'GROESBECK POND',
    'Recycle': 'RECYCLING WELL',
    'Electric': 'ELECTRIC WELL',
    'Cooper 1': 'COOPER-1',
    'Cooper 2': 'COOPER-2',
    'MW-3sr': 'MW-03sr',
    'MW-3dr': 'MW-03dr',
    'MW-5sr': 'MW-05sr',
    'MW-5dr': 'MW-05dr',
    'MW-6dr': 'MW-06dr',
    'MW-6sr': 'MW-06sr',
    "MW-9r" : "MW-09r",
    "P28r" : "P-28r",
    "P29r2" : "P-29r2",
    "MW-6r2" : "MW-06r2",
    'SW1' : "SW-1",
    'SW2' : "SW-2",
    'SW3' : "SW-3",
}

edd_to_db_methods = {
    'Calculation': 'CALC',  
    'ASTM D7511-12': 'ASTM D7511-09e2',
    'EPA 200.8 Rev. 5.4': 'E200.8',
    'EPA 200.8': 'E200.8',
    'EPA 200.7 Rev. 4.4': 'E200.7',
    'EPA 245.1': 'E245.1',
    'EPA 245.1 Rev. 3.0': 'E245.1',
    'EPA 300.0 Rev. 2.1': 'E300.0',
    'EPA 350.1 Rev. 2.0': 'E350.1',
    'EPA 410.4 Rev. 2.0': 'E410.4',
    'EPA 420.1': 'E420.1',
    'EPA 624.1': 'E624.1',
    'EPA 8260D': 'SW8260D',
    'EPA 9056A': 'SW9056A',
    'EPA 6020B': 'SW6020B',
    'Calculation': 'CALC',
    'SM 2510 B-2011': 'SM2510B',
    'SM 2320 B-2021': 'SM2320B',
    'SM 2320 B-21': 'SM2320B',
    'SM 2540 C-20': 'SM2540C-20',
    'SM 2540 C-2020': 'SM2540C-20',
    'SM 4500-Cl D-21': 'SM4500 CL-D',
    'SM 4500-H+ B-2011': 'SM4500-H+',
    'SM 4500-H+ B 2011': 'SM4500-H+',
    'SM 4500 NH3 G': 'SM4500 NH3-G',
    'SM 5210B-2016': 'SM5210B',
    'SM 5310 B-14': 'SM5310B',
    'SM 5310B-2014': 'SM5310B',
    'Hach 8000': 'HACH 8000',
}

edd_to_db_Prepmethods = {
    'EPA 200.2 (Dissolved)': 'E200.2',
    'EPA 200.2': 'E200.2',
    'EPA 5030B': 'SW5030B',
    'EPA 300.0/9056A': 'Method',
    'Hach 8000': 'Method',
    'SM 2320 B-2021': 'Method',
    'SM 2510 B-2011': 'Method',
    'SM 4500 NH3 G': 'Method',
    'SM 4500-H+ B-2011': 'Method',
    'SM 5310B-2014': 'Method',
    'ASTM D7511-12': 'Method',
    'EPA 7470A/EPA 245.1': 'Method',
    'EPA 420.1': 'Method',
    'SM 5210B-2016': 'Method',
}


chemical_name_dict = {
    "Bicarbonate Alkalinity as CaCO3 at pH 4.5": "Alkalinity, bicarbonate, to pH 4.5",
    "1,2-Dibromo-3-chloropropane (SIM)": "1,2-Dibromo-3-chloropropane",
    "Bromoform (SIM)": "Bromoform",
    'Methyl Iodide': 'Iodomethane',
    "t-Butanol": "tert-Butanol",
    "Xylenes": "Xylenes,total",
    "Ethylene Dibromide": "1,2-Dibromoethane",
    'trans-1,4-Dichloro-2-butene (SIM)': 'trans-1,4-Dichloro-2-butene',
    'Arsenic, Dissolved': 'Arsenic',
    "Boron, Dissolved": "Boron",
}

lab_matrix_dict = {
    'Ground Water': 'WG',
    'Aqueous': 'WU',
    'Water': 'WU',
}

result_unit_dict = {

    'pH Units': "Su",
    '°C': "Deg C",
}

analytes_cas_dict = {
    "Arsenic": "7440-38-2",
    "Boron": "7440-42-8",
    "Beryllium": "7440-41-7",
    "Calcium": "7440-70-2",
    "Cadmium": "7440-43-9",
    "Iron": "7439-89-6",
    "Chromium": "7440-47-3",
    "Copper": "7440-50-8",
    "Magnesium": "7439-95-4",
    "Phosphorus": "7723-14-0",
    "Potassium": "7440-09-7",
    "Manganese": "7439-96-5",
    "Mercury": "7439-97-6",
    "Nickel": "7440-02-0",
    "Sodium": "7440-23-5",
    "Chloromethane": "74-87-3",
    "Vinyl chloride": "75-01-4",
    "Bromomethane": "74-83-9",
    "Chloroethane": "75-00-3",
    "Trichlorofluoromethane": "75-69-4",
    "1,1-Dichloroethene": "75-35-4",
    "Acetone": "67-64-1",
    "Iodomethane": "74-88-4",
    "Carbon disulfide": "75-15-0",
    "Methylene chloride": "75-09-2",
    "Acrylonitrile": "107-13-1",
    "1,1-Dichloroethane": "75-34-3",
    "Vinyl acetate": "108-05-4",
    "2-Butanone": "78-93-3",
    "cis-1,2-Dichloroethene": "156-59-2",
    "Bromochloromethane": "74-97-5",
    "Chloroform": "67-66-3",
    "1,1,1-Trichloroethane": "71-55-6",
    "Carbon tetrachloride": "56-23-5",
    "Benzene": "71-43-2",
    "1,2-Dichloroethane": "107-06-2",
    "Trichloroethene": "79-01-6",
    "1,2-Dichloropropane": "78-87-5",
    "Dibromomethane": "74-95-3",
    "Bromodichloromethane": "75-27-4",
    "cis-1,3-Dichloropropene": "10061-01-5",
    "4-Methyl-2-pentanone": "108-10-1",
    "Toluene": "108-88-3",
    "trans-1,3-Dichloropropene": "10061-02-6",
    "1,1,2-Trichloroethane": "79-00-5",
    "Tetrachloroethene": "127-18-4",
    "2-Hexanone": "591-78-6",
    "Dibromochloromethane": "124-48-1",
    "1,2-Dibromoethane (EDB)": "106-93-4",
    "Chlorobenzene": "108-90-7",
    "1,1,1,2-Tetrachloroethane": "630-20-6",
    "Ethylbenzene": "100-41-4",
    "m,p-Xylene": "179601-23-1",
    "o-Xylene": "95-47-6",
    "Xylenes, total": "1330-20-7",
    "Styrene": "100-42-5",
    "Bromoform": "75-25-2",
    "1,1,2,2-Tetrachloroethane": "79-34-5",
    "1,2,3-Trichloropropane": "96-18-4",
    "trans-1,4-Dichloro-2-butene": "110-57-6",
    "1,4-Dichlorobenzene": "106-46-7",
    "1,2-Dichlorobenzene": "95-50-1",
    "1,2-Dibromo-3-chloropropane": "96-12-8",
    "1,2-Dichloroethane-d4": "17060-07-0",
    "Toluene-d8": "2037-26-5",
    "4-Bromofluorobenzene": "460-00-4",
    "1,2-Dichlorobenzene-d4": "2199-69-1",
    "Total Inorganic Nitrogen": "InorgN",
    "Ammonia as N": "7664-41-7",
    "Total Dissolved Solids": "TDS",
    "Bicarbonate Alkalinity as CaCO3 at pH 4.5": "ALKB4.5",
    "Alkalinity, bicarbonate, to pH 4.5": "ALKB4.5",
    "Bicarbonate Alkalinity": "ALKB",
    "Carbonate Alkalinity as CaCO3 at pH 8.2": "ALK8.3",
    "Specific Conductance": "SpCond-L",
    "Temperature C": "Temp",
    "Total Organic Carbon": "TOC",
    "Chloride": "16887-00-6",
    "Nitrate as N": "14797-55-8",
    "Nitrate-N": "14797-55-8",
    "Nitrite as N": "14797-65-0",
    "Nitrite-N": "14797-65-0",
    "Sulfate as SO4": "14808-79-8",
    "Barium": "7440-39-3",
    "Antimony": "7440-36-0",
    "Lithium": "7439-93-2",
    "Chemical Oxygen Demand": "COD",
    "Selenium": "7782-49-2",
    "1,2,4-Trimethylbenzene": "95-63-6",
    "1,2-Dibromo-3-chloropropane": "96-12-8",
    "Carbon Disulfide": "75-15-0",
    "Carbon Tetrachloride": "56-23-5",
    "Iodomethane": "74-88-4",
    "tert-Butanol": "75-65-0",
    "trans-1,2-Dichloroethene": "156-60-5",
    "Vinyl Acetate": "108-05-4",
    "Xylenes,total": "1330-20-7",
    "1,2-Dibromoethane": "106-93-4",
    "Methylene Chloride": "75-09-2",
    "Tetrahydrofuran": "109-99-9",
    "trans-1,4-Dichloro-2-butene": "110-57-6",
    "Vinyl Chloride": "75-01-4",
    "Arsenic": "7440-38-2",
    "Total Phenolics": "TRPhen",
    "Biochemical Oxygen Demand": "BOD",
    "NMeFOSAA": "2355-31-9",
    "NEtFOSAA": "2991-50-6",
    "13C7-PFUnA": "13C7-PFUnA",
    "13C2-PFDoDA": "13C2-PFDoDA",
    "13C2-4:2 FTS": "13C2-4:2 FTS",
    "13C2-6:2 FTS": "13C2-6:2 FTS",
    "13C2-8:2 FTS": "13C2-8:2 FTS",
    "13C8-FOSA": "13C8-FOSA",
}