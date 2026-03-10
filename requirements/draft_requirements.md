Task: Create a siting report which assesses the potential of coal power plants to host SMRs in the future within the region.
The region is defined as: Central, Eastern, Southern Europe, including Romania, Serbia, Armenia. For Romania, on top of the coal power plants sites other two sites should be evaluated: 1. Braila - Chiscani (thermal power plant) and 2. FPCU Feldioara

Deliverable 1: The aim is to identify a list of between 12-20 viable sites, with an ideal spot on 15 sites.

Deliverable 2: A report which details each of the sites based on international siting criteria (IAEA and EPRI). The report will argue for the business case of building NuScale-6 of 462 MW on these sites and the benefits that Nuclearelectrica can have by building the FOAK of this SMR in Romania by then selling expertise (and any other possible benefits - identify via benefits map) to other countries or companies implementing such technology.

Planning:

1. Identify the IAEA procedures for siting (SSG 35);
   1.1 Read and create shortcut-mapping files for the procedure in order to quickly access parts of the file for token saving purposes. Output the mapping in an md file within document_maps folder.
2. Identify the EPRI procedures for siting
3. Identify the main criteria for siting on each of the main phases:
   a. site survey;
   b. screening;
   c. candidate sites;
4. Create the scoring matrix taking the criteria into account
5. Identify the required databases for obtaining data for each criteria in part.
6. Identify a method of connecting to each of the said database
7. Evaluate the suitability of each database and establish limitations. Establish if the data is suitable.

Build an automated system of site evaluation:

1. plan and ingest the available power plants database: <file> and turn it into a postgres database so we can work with it programatically.
2. Plan on how to update via websearches the status of each power plant in turn in order to validate all of the current data. The status is defined as all pieces of information from the power plant database: <file>
3. Plan and develop the required back-end code in order to connect to each of the required databases in order to obtain information for each evaluation criteria in part. Make sure to respect all software development steps in order to ensure good functioning.
