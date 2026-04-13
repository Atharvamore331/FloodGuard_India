import pandas as pd
import numpy as np 
from functools import reduce

d1 = pd.read_excel('sm_Arunachalpradesh_cleaned.csv.xlsx')
d2 = pd.read_excel('sm_assam_cleaned.csv.xlsx')
d3 = pd.read_excel('sm_Bihar_cleaned.csv.xlsx')
d4 = pd.read_excel('sm_Chnadigarh_cleaned.csv.xlsx')
d5 = pd.read_excel('sm_Chhattisgarh.csv.xlsx')
d6 = pd.read_excel('sm_Dadranagarhav_cleaned.csv.xlsx')
d7 = pd.read_excel('sm_DamanandDiu_cleaned_2020.csv.xlsx')
d8 = pd.read_excel('sm_Delhi_2020.csv.xlsx')
d9 = pd.read_excel('sm_Goa_cleaned.csv.xlsx')
d10 = pd.read_excel('sm_Gujarat_cleaned.csv.xlsx')
d11= pd.read_excel('sm_haryana_cleaned.csv.xlsx')
d12= pd.read_excel('sm_himachalPradesh_cleaned.csv.xlsx')
d13= pd.read_excel('sm_JammuandKashmir_cleaned.csv.xlsx')
d14= pd.read_excel('sm_Jharkhand_cleaned.csv.xlsx')
d15= pd.read_excel('sm_Karnataka_cleaned.csv.xlsx')
d16= pd.read_excel('sm_Kerala_cleaned.csv.xlsx')
d17= pd.read_excel('sm_Ladakh_2020_cleaned.csv.xlsx')
d18= pd.read_excel('sm_Lakshdweep_2020_cleaned.csv.xlsx')
d19= pd.read_excel('sm_MadhyaPradesh_2020.csv.xlsx')
d20= pd.read_excel('sm_Maharashtra_2020.csv.xlsx')
d21= pd.read_excel('sm_Manipur_2020_cleaned.csv.xlsx')
d22= pd.read_excel('sm_Meghalaya_2020_cleaned.csv.xlsx')
d23= pd.read_excel('sm_Mizoram_2020_cleaned.csv.xlsx')
d24= pd.read_excel('sm_Nagaland_2020_cleaned.csv.xlsx')
d25= pd.read_excel('sm_Odisha_2020_cleaned.csv.xlsx')
d26= pd.read_excel('sm_Pondicherry_2020_cleaned.csv.xlsx')
d27= pd.read_excel('sm_rajasthan_2020_cleaned.csv.xlsx')
d28= pd.read_excel('sm_Sikkim_2020_cleaned.csv.xlsx')
d29= pd.read_excel('sm_Tamilnadu_2020_cleaned.csv.xlsx')
d30= pd.read_excel('sm_Telangana_2020_cleaned.csv.xlsx')
d31= pd.read_excel('sm_Tripura_2020_cleaned.csv.xlsx')
d32= pd.read_excel('sm_Uttarakhand_cleaned.csv.xlsx')

datasets = [d1, d2, d3, d4, d5, d6, d7, d8, d9, d10,
            d11, d12, d13, d14, d15, d16, d17, d18, d19, d20,
            d21, d22, d23, d24, d25, d26, d27, d28, d29, d30,
            d31, d32]

for i, df in enumerate(datasets, start=1):
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')


merged_df = pd.concat(datasets, ignore_index=True)
merged_df.to_csv("merged.csv", index=False)


