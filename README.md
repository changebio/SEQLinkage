# SEQLinkage
> Collapsed Haplotype Pattern Method for Linkage Analysis of Next-Generation Sequencing Data


## Pre-requisites

Make sure you install the pre-requisited before running seqlink:

```
conda install -c conda-forge xeus-cling
conda install -c anaconda swig 
conda install -c conda-forge gsl
pip install egglib
git clone https://github.com/statgenetics/cstatgen.git
cd cstatgen
python setup.py install
```

## Install

`pip install SEQLinkage`

## How to use

### 1. Test on seqlinkage-example

```
seqlink --fam seqlinkage-example.fam --vcf seqlinkage-example.vcf.gz -f MERLIN --output RMBPt8 --jobs 8

seqlink --fam seqlinkage-example.fam --vcf seqlinkage-example.vcf.gz -f MERLIN --output RMB0 --jobs 8 --bin 0

seqlink --fam seqlinkage-example.fam --vcf seqlinkage-example.vcf.gz -f MERLIN --output RMB1 --jobs 8 --bin 1

seqlink --fam seqlinkage-example.fam --vcf seqlinkage-example.vcf.gz --freq EVSEAAF -o LinkageAnalysis -K 0.001 --moi AR -W 0 -M 1 --theta-max 0.5 --theta-inc 0.05 -j 8 --run-linkage
```

### 2. Test on AD family

```
seqlink --fam data/mwe_normal_fam.csv --vcf data/first1000snp_full_samples.vcf.gz -f LINKAGE --blueprint data/genemap.hg38.txt --freq AF -K 0.001 --moi AD -W 0 -M 1

seqlink --fam data/mwe_normal_fam.csv --vcf data/first1000snp_full_samples.vcf.gz -f MERLIN --blueprint data/genemap.hg38.txt --freq AF
```

```
./seqlink --fam seqlinkage-example/seqlinkage-example.fam --vcf seqlinkage-example/seqlinkage-example.vcf.gz -f MERLIN --blueprint data/genemap.txt --freq EVSEAAF -o seqtest
./seqlink --fam data/new_trim_ped_famless17.fam --vcf data/first1000snp_full_samples.vcf.gz -f MERLIN --blueprint data/genemap.hg38.txt --freq AF
```

./seqlink --fam data/new_trim_ped_famless17.fam --vcf data/first1000snp_full_samples.vcf.gz -f MERLIN --blueprint data/genemap.hg38.txt --freq AF -K 0.001 --moi AD -W 0 -M 1 --run-linkage

./seqlink --fam data/Example_data/pedigree.fam --vcf data/Example_data/example.vcf.gz -f MERLIN MEGA2 PLINK LINKAGE --build hg38 --chrom-prefix chr --freq AF -o data/Example_data/output -K 0.001 --moi AD -W 0 -M 1


./seqlink --fam data/mwe_normal_fam.csv --vcf data/first1000snp_full_samples.vcf.gz --anno data/first1000_chr1_multianno.csv --pop data/full_sample_fam_pop.txt -f MERLIN MEGA2 PLINK LINKAGE --build hg38 --freq AF -o data/first1000test -K 0.001 --moi AD -W 0 -M 1

./seqlink --fam data/new_trim_ped_famless17_no\:xx.fam --vcf /mnt/mfs/statgen/alzheimers-family/linkage_files/geno/full_sample/vcf/full_sample.vcf.gz --anno MWE/annotation/EFIGA_NIALOAD_chr1.hg38.hg38_multianno.csv --pop data/full_sample_fam_pop.txt -f MERLIN MEGA2 PLINK LINKAGE --build hg38 --freq AF -o data/fullchr1data -K 0.001 --moi AD -W 0 -M 1 -j 4

## Testing output

seqlink --fam seqlinkage-example/seqlinkage-example.fam --vcf seqlinkage-example/seqlinkage-example.vcf.gz -f MERLIN MEGA2 PLINK LINKAGE --blueprint data/genemap.txt --freq EVSEAAF -o data/seqtest_20220221 -K 0.001 --moi AD -W 0 -M 1 -j 4

seqlink --fam data/new_trim_ped_famless17_no:xx.fam --vcf /mnt/mfs/statgen/alzheimers-family/linkage_files/geno/full_sample/vcf/full_sample.vcf.gz --anno MWE/annotation/EFIGA_NIALOAD_chr22.hg38.hg38_multianno.csv --pop data/full_sample_fam_pop.txt -f MERLIN MEGA2 PLINK LINKAGE --build hg38 --freq AF -o data/fullchr22data -K 0.001 --moi AD -W 0 -M 1 -j 8

```python
import pandas as pd
```

```python
tmp = pd.read_csv('../data/genemap.hg38.txt',sep='\t',header=None)
```

```python
tmp
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>0</th>
      <th>1</th>
      <th>2</th>
      <th>3</th>
      <th>4</th>
      <th>5</th>
      <th>6</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>11868</td>
      <td>14362</td>
      <td>LOC102725121@1</td>
      <td>9.177127e-07</td>
      <td>0.000001</td>
      <td>6.814189e-07</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1</td>
      <td>11873</td>
      <td>14409</td>
      <td>DDX11L1</td>
      <td>9.195321e-07</td>
      <td>0.000001</td>
      <td>6.827698e-07</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1</td>
      <td>14361</td>
      <td>29370</td>
      <td>WASH7P</td>
      <td>1.529988e-06</td>
      <td>0.000002</td>
      <td>1.136045e-06</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1</td>
      <td>17368</td>
      <td>17436</td>
      <td>MIR6859-1@1,MIR6859-2@1,MIR6859-3@1,MIR6859-4@1</td>
      <td>1.217693e-06</td>
      <td>0.000002</td>
      <td>9.041595e-07</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1</td>
      <td>30365</td>
      <td>30503</td>
      <td>MIR1302-10@1,MIR1302-11@1,MIR1302-2@1,MIR1302-9@1</td>
      <td>2.129597e-06</td>
      <td>0.000003</td>
      <td>1.581266e-06</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>28320</th>
      <td>X</td>
      <td>155612564</td>
      <td>155782457</td>
      <td>SPRY3</td>
      <td>NaN</td>
      <td>196.056662</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>28321</th>
      <td>X</td>
      <td>155881344</td>
      <td>155943769</td>
      <td>VAMP7</td>
      <td>NaN</td>
      <td>196.190010</td>
      <td>5.600000e+01</td>
    </tr>
    <tr>
      <th>28322</th>
      <td>X</td>
      <td>155997695</td>
      <td>156010817</td>
      <td>IL9R</td>
      <td>NaN</td>
      <td>196.305985</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>28323</th>
      <td>X</td>
      <td>156014563</td>
      <td>156016830</td>
      <td>WASIR1</td>
      <td>NaN</td>
      <td>196.320452</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>28324</th>
      <td>X</td>
      <td>156025657</td>
      <td>156028183</td>
      <td>DDX11L16</td>
      <td>NaN</td>
      <td>196.334645</td>
      <td>NaN</td>
    </tr>
  </tbody>
</table>
<p>28325 rows × 7 columns</p>
</div>



```python
tmp[0].value_counts()
```




    1                      2809
    2                      1816
    19                     1779
    11                     1678
    17                     1583
    3                      1560
    6                      1453
    12                     1386
    7                      1359
    5                      1314
    X                      1209
    16                     1177
    9                      1119
    10                     1107
    4                      1091
    8                      1056
    15                     1012
    14                      946
    20                      774
    22                      646
    13                      629
    18                      436
    21                      374
    17_KI270909v1_alt         3
    22_KI270879v1_alt         3
    7_KI270803v1_alt          2
    15_KI270850v1_alt         2
    4_GL000008v2_random       1
    1_KI270706v1_random       1
    Name: 0, dtype: int64



```python
tmp1 = tmp[tmp[0]=='22']
```

```python
tmp1[tmp1[3]=='LINC01664']
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>0</th>
      <th>1</th>
      <th>2</th>
      <th>3</th>
      <th>4</th>
      <th>5</th>
      <th>6</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>26484</th>
      <td>22</td>
      <td>17121594</td>
      <td>17132104</td>
      <td>LINC01664</td>
      <td>3.496778</td>
      <td>5.134655</td>
      <td>1.946244</td>
    </tr>
  </tbody>
</table>
</div>



```python
tmp1[tmp1[3]=='BID']
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>0</th>
      <th>1</th>
      <th>2</th>
      <th>3</th>
      <th>4</th>
      <th>5</th>
      <th>6</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>26493</th>
      <td>22</td>
      <td>17734139</td>
      <td>17774665</td>
      <td>BID</td>
      <td>7.132236</td>
      <td>10.196359</td>
      <td>4.192282</td>
    </tr>
  </tbody>
</table>
</div>



```python
tmp1[tmp1[3]=='RTL10']
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>0</th>
      <th>1</th>
      <th>2</th>
      <th>3</th>
      <th>4</th>
      <th>5</th>
      <th>6</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>26535</th>
      <td>22</td>
      <td>19846145</td>
      <td>19854874</td>
      <td>RTL10</td>
      <td>12.136091</td>
      <td>16.519006</td>
      <td>8.210012</td>
    </tr>
  </tbody>
</table>
</div>



```python
tmp1
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>0</th>
      <th>1</th>
      <th>2</th>
      <th>3</th>
      <th>4</th>
      <th>5</th>
      <th>6</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>26467</th>
      <td>22</td>
      <td>15784953</td>
      <td>15827434</td>
      <td>DUXAP8</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
    </tr>
    <tr>
      <th>26468</th>
      <td>22</td>
      <td>15805697</td>
      <td>15820884</td>
      <td>BMS1P22@3</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
    </tr>
    <tr>
      <th>26469</th>
      <td>22</td>
      <td>15805697</td>
      <td>15815897</td>
      <td>BMS1P17@3,BMS1P18@3</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
    </tr>
    <tr>
      <th>26470</th>
      <td>22</td>
      <td>15740892</td>
      <td>15778287</td>
      <td>PSLNR</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
    </tr>
    <tr>
      <th>26471</th>
      <td>22</td>
      <td>15690025</td>
      <td>15721631</td>
      <td>POTEH</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>27111</th>
      <td>22</td>
      <td>50674390</td>
      <td>50733212</td>
      <td>SHANK3</td>
      <td>79.970067</td>
      <td>90.409669</td>
      <td>70.999029</td>
    </tr>
    <tr>
      <th>27112</th>
      <td>22</td>
      <td>50735828</td>
      <td>50738169</td>
      <td>LOC105373100</td>
      <td>80.037493</td>
      <td>90.485907</td>
      <td>71.073657</td>
    </tr>
    <tr>
      <th>27113</th>
      <td>22</td>
      <td>50738203</td>
      <td>50745339</td>
      <td>ACR</td>
      <td>80.044958</td>
      <td>90.494347</td>
      <td>71.080286</td>
    </tr>
    <tr>
      <th>27114</th>
      <td>22</td>
      <td>50757085</td>
      <td>50799637</td>
      <td>RPL23AP82</td>
      <td>80.102184</td>
      <td>90.559043</td>
      <td>71.131103</td>
    </tr>
    <tr>
      <th>27115</th>
      <td>22</td>
      <td>50767506</td>
      <td>50783636</td>
      <td>RABL2B</td>
      <td>80.097821</td>
      <td>90.554110</td>
      <td>71.127228</td>
    </tr>
  </tbody>
</table>
<p>646 rows × 7 columns</p>
</div>



```python
535-467
```




    68


