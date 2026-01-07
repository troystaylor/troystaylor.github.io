---
title: "Power Platform IndiePubs: Badgr Custom Connector"
author: Troy Taylor
date: 2021-02-17
category: Power Platform
layout: post
---

Creating my first custom connector for Badgr, I realized I wanted to share my workflow and what I've learned. Looking at the API guides or API itself, you will find they have the structure to build a connector already done. You will find different types of APIs, and the ones I prefer to work with have the OpenAPI or Swagger files prepared for you. Once you import those files into a custom connector in Power Automate, you will have a custom connector that works (or at least looks like it does).

*I am not going to talk about API authentication or different API types in this post. I feel that there are already existing great guides you can read and I am focusing on the Power Platform integration.* 

At this point in the process, you may think that building a custom connector is finished. You can run an action or two, see that the test runs successfully without an error, and off you go to build your Power App or Power Automate flow. During the several weeks after trying to use the custom connector in a flow, you will realize that not all actions work. Or worse, you realize the connector has so many actions that perhaps you should have tested more thoroughly. During the couple of days you put a flow together and tested, you also could have built validation checks into the connector. Rather than manually pulling out the API parameter list and validating whether each is an input or an output or both, you should have used the Power Platform CLI to download the file and work with it in your favorite code editor.

Continuing on, you've downloaded the connector and you can start adding user-facing titles to every parameter and improve the descriptions with better wording than the original API documentation. You have a couple of options: keep building and testing within the custom connector editor or go file spelunking for the icons and icons background colors for services you are using. You've decided to do both at the same time and you spend several hours making every action just a little bit better. 

And then you'll see several different actions which do the same thing like List vs Get, but perhaps these actions are configured to make single API requests, but you really would like to call the API 5 times with different parameters during a single action call. So instead, you can create an action that is capable of calling the API 5 times and use loops inside Power Automate to iterate through those actions. 

For my first custom connector submission, I fixed many of the simple parameter names and added pagination. I submitted it to [Microsoft's Power Platform Connectors repository](https://github.com/microsoft/PowerPlatformConnectors) using a [pull request](https://github.com/microsoft/PowerPlatformConnectors/pull/500) and the code was reviewed, checked, and errors were corrected. I had a working certified connector two weeks after my submission.
