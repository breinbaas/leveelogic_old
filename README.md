## LeveeLogic

Code for levee assessments by Rob van Putten | LeveeLogic

This code will slowly replace our old code and make it publicly available under the GPLv3 license. This code is based on years of experience in levee assessments and automation and makes use of some spezialized packages like d-geolib and other code that has been created by the community of Dutch geotechnical engineers. One thing; **don't blame me or my code if your structure fails.. never trust a computer (too much)** ;-)

**TIP** You can learn a lot of how to use the leveelogic package by looking at the test code which you can find under the tests/ path

## Functionality

### Soon to be added 

For users;
 
* [X] Cpts
* [ ] Boreholes
* [ ] DStability interaction / serialization / parsing / editing
* [ ] Crosssections
* [ ] Geotechnical profiles

For developers;

* [ ] Automated packaging for pip install
* [ ] Automated testing CI/CD

and more... 

**NOTE** This code will be written in my sparetime so don't go pushing me unless you are willing to pay. I am making an effort to create something that is easy to use and has decent documentation and this takes time.

### CPT

#### Reading

You can read CPT files that are formated in the GEF or XML format. Loading the cpts is easy;

```python:
cpt = Cpt.from_file("mycpt.gef")
cpt = Cpt.from_file("mycpt.xml")
```

If you like to work with online data you will be happy to know that this package also provides a ```from_string``` option. Just don't forget to add the right suffix;

```python:
cpt = Cpt.from_string(s, suffix=".gef")
cpt = Cpt.from_string(s, suffix=".xml")
```

and finally, if you work in The Netherlands and would like to get CPT's from the BRO API you can simply type;

```python
cpt = Cpt.from_bro_id("CPT000000097074")
```

You just need to find the CPT id online and yes, we will be adding the option to download CPTs based on a geographical location later.

#### Interpretation

We have implemented three interpretation options;

* three type rule (sand, clay or peat) 
* CUR166 based on electrical cone and friction ratio
* My implementation of Robertson (not using the waterpressure)

Calling these will give you a SoilProfile1 object (1D soil structure) like so;

```python
cpt.to_soilprofile1()
```

You will have to set the interpretation method (CptConversionMethod) using on of these options;

* CptConversionMethod.THREE_TYPE_RULE being the three type rule
* CptConversionMethod.NL_RF being the CUR166 based on electrical cone and friction ratio
* CptConversionMethod.ROBERTSON being my implementation of the Robertson correlation

You can also state the minimum layerheight, the peat friction ratio and if you want the predrilled layer to be added to the result. Here is an example;

```python
cpt.to_soilprofile1(
    cptconversionmethod = CptConversionMethod.ROBERTSON,
    minimum_layerheight = 0.4,
    peat_friction_ratio = 5.0,
)
```

This will generate a SoilProfile1 object using the Robertson correlation, creating layers that are at least 0.4m thick and all measurements where the friction ration is equal to or above 5.0 will be converted to peat.

You can use the soillayers property of the SoilProfile1 object to see which soillayers were created.

#### Plotting

You can plot the CPT in multiple ways;

Really barebones;

```python
cpt.plot(filename=f"bro_cpt_download.png")
```

which will lead to a plot like this;

![Barebones plot of the CPT](img/bro_cpt.gef.png)

or you can use one of the three CptConversion methods. An example of using the Robertson interpretation would be;

```python
cpt.plot(
    "cpt_robertson_classification.png",
    cptconversionmethod=CptConversionMethod.ROBERTSON,
)
```

![Robertson](img/cpt_robertson_classification.png)

It is possible to define the minimum layer height so you get a managable amount of soillayers;

```python
cpt.plot(
    "cpt_robertson_classification_1m.png",
    cptconversionmethod=CptConversionMethod.ROBERTSON,
    minimum_layerheight=1.0,
)
```

It is also possible to override the Robertson interpretation with a simple rule that defines soil as peat if it is above a threshold for the friction ratio, this looks like the following code;

```python
cpt.plot(
    "cpt_robertson_classification_1m.png",
    cptconversionmethod=CptConversionMethod.ROBERTSON,
    minimum_layerheight=1.0,
    peat_friction_ratio=4.0,
)
```

This leads to the following plot;

![Robertson](img/cpt_robertson_with_peat_classification_1m.png)

In the previous case all measurements with a friction ratio of 4.0 or higher will be interpreted as being peat.

There is also an option to create an SBT index plot using the following code;

```python
cpt.plot_Ic("cpt_Ic_plot.png")
```

![Robertson](img/cpt_Ic_plot.png)


**DISCLAIMER**
The interpretation options of CPTs are endless and can be very specific for the region you are working in. For me these interpretation methods have proven their value but always check if they work for you!

## Credits

Credits go to;

* Deltares for the d-geolib package
* Thomas van der Linden for the gefxmlreader (I hate xml parsing ;-)