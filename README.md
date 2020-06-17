# nmr-star-dictionary-scripts

Internal: scripts that read NMR-STAR dictionary as CSV files and generate dictionaries that drive various pieces of BMRB software.

The pieces:
  * (now defunct) ADIT-NMR
  * NMR-STAR relational database
  * BMRB entry validation and entry replease software

The files:
  * ''conf/*'' - config files driving the converter, DDL SQL scripts
  * ''doc/*'' - various documents, not all of them current
  * ''input/*'' - input files, for reference (fetch up-to-date ones from nmr-star-dictionary on github)
  * ''scripts/*'' - the code
  * ''webfront/*'' - dictionary browser on the website (PHP)
