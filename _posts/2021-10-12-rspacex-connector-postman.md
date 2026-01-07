---
title: "Power Platform IndiePubs: Creating a r/SpaceX connector from a Postman collection"
author: Troy Taylor
date: 2021-10-12
category: Power Platform
layout: post
---

Like many of you, two weeks ago I had the Powerful Devs online conference up on my second screen while working on a client project. I was mostly interested in hearing from Charles Lamanna, but I found myself drawn into the presentation from [Linda Nichols](https://twitter.com/lynnaloo), ["Using Space APIs to Create Out of This World Power Apps."](https://channel9.msdn.com/Events/Microsoft-Power-Platform/Powerful-Devs-Conference/Using-Space-APIs-to-Create-Out-of-This-World-Power-Apps-with-Linda-Nichols) When it comes to custom connectors, I'm primarily focused on Power Automate, but as a consultant, I'm aware of the differences with Logic Apps and the other API offering available in Azure.

### The power is yours - Pro-dev, low-code, or fusion dev

Linda's approach to surfacing the r/SpaceX APIs in a Power App is the same method I hear many developers use - use a function to handle the API calls and then secure the response behind Azure API Management. 

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1632576733283/8BJUi8Ioy.png)

APIM has incredible scalability and allows you to shape multiple APIs for the data you need in your end project. It will require you to stand up two (or more) resources, which will operate at a very low cost. If you haven't already, stop right now and watch Linda's recorded presentation. Her method of implementing a connector for Power Apps is spot-on for an organization needing a connector for an internal project or system.


### Let's lower the barrier to orbit

Immediately following Linda's presentation, I started looking at smaller NASA APIs and picked EONET as the first Independent Publisher connector to build, but while I was building that one, I kept thinking about the presentation's use of the r/SpaceX API and then I looked to see if a connector was already available. When I saw that no one had built one, I reached out to Linda on Twitter to make sure that she wasn't already building it, and instead got her blessing to go ahead.

This SpaceX API is unofficial and the contributors host it on [GitHub](https://github.com/r-spacex/SpaceX-API). The documentation is pretty good with each operation given its own file with detailed response schemas. There are links for API clients and apps using the API. But I was most happy to find a Postman collection, which (fingers crossed) opened with the newest version (v4) of all the operations separated by folders. I tested a few of the operations to make sure it was working and then removed any create or update operators (as those require an API key and wouldn't be for my target audience), then saved the collection to a local file.

This file, a Postman collection v2.1, uploaded to Power Automate custom connectors just fine. I again tested the operations again, noticing that the query parameters were mostly all in the correct format, but as expected, there were no response schemas. Once again, with anything open source, beggars can't be choosers.

### In space, no one can hear you document response schemas

At this point, the hardest part for me (and probably most Independent Publishers) continues to be defining response schemas. Even if you use the custom connector editor in Power Automate to generate the response, there are still errors to correct. First, you're going to have to take all of the response descriptions and rename the description to be the title. You'll still need to convert the title to [title case](https://apastyle.apa.org/style-grammar-guidelines/capitalization/title-case), but at least you start with something instead of a blank. Speaking of blanks, if you add a double quotation mark and a comma and a line break to the originally generated description, this will give you a blank description. As required for the Independent Publisher certification, you will need to now give a proper sentence for the description. I highly recommend if the API service has provided standardized descriptions, you should use those.

With the r/SpaceX API, I wasn't expecting there to be so many response structural differences. So out of the 1400 empty descriptions, there were perhaps a couple hundred that were easily found and replaced. I usually expect to complete 200-250 descriptions using find and replace, but in this case, I don't think I cracked 100 an hour. But a week later, they are done and the connector is now submitted.

### Don't print the response, show me

I'm very fortunate to work with [Hardit Bhatia](https://twitter.com/thepoweraddict) and around the same time that I starting working on the r/SpaceX connector, Hardit published a tutorial for his [Pinterest-like gallery](https://thepoweraddict.com/how-to-create-a-pinterest-like-gallery/). I built a very simple gallery example for my Placedog connector, so this was the perfect opportunity to built Hardit's example.

I was able to use his Boards app to get some of the functionality, I needed, but ultimately Hardit helped me optimize the loading of 20 images at a time:

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1633995473368/FXDkaVdz_.png)

You may notice some of the images are repeating - that is my fault, not Hardit's, with the way in which I randomized the available images available from the API. The other screen I built for the demo is a launch countdown timer and that's available in the [next blog post](https://www.troystaylor.com/power-platform-indiepubs-creating-a-rspacex-launch-countdown-clock).
