---
title: "Power Platform IndiePubs: Creating an Okta connector using Postman Collections"
author: Troy Taylor
date: 2021-09-13
category: Power Platform
layout: post
---

Last week while doomscrolling (as you do), I saw [Phil Topness](https://twitter.com/topness)'s tweet of a Power Automate custom connector 'Import a Postman collection' function [screenshot](https://twitter.com/topness/status/1434289962741075969). When dealing with APIs, Postman should be your best friend for testing authentication and organizing actions. So I'm certainly familiar with it (I have it pinned on my taskbar between Atom and XRMToolBox), but after experimenting with V1 collections last year for a custom connector with no success, I prefer to build custom connectors by hand or with an OpenAPI file.

### Let's get this collection started

When Okta was added to the [Top Connector Asks](https://github.com/microsoft/PowerPlatformConnectors/wiki/Top-Connector-Asks), I was intrigued because I had looked at creating a connector for [Auth0](https://auth0.com/docs/api) but couldn't come up with a use case for it. Auth0 and Okta are similar in that they both provide authentication for apps and services, but Okta is focused more on enterprise usage (with enterprise pricing), while Auth0 focuses more on developers, nonprofits, and small businesses.

Starting on the Okta [developer site](https://developer.okta.com/), you find quite the collection of guides and SDKs to kickstart your implementation of Okta. Under the Reference section after reading several of the overview sections, I found a section of prepared Postman Collections ready for you to import and get started. While keeping in mind that I might run into the 512 reference limit I hit with Xero Accounting, I started importing all of the collections.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1631283532043/jkR61kusY.png)

Since there are 28 collections, I decided to make a new workspace within Postman. 

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1631283689370/BJY7ciKEm.png)

This spacehero won't be alone for long:

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1631283892117/nmq5NTDNK.png)

After importing all the collections, I followed the [REST instructions](https://developer.okta.com/code/rest/) to import a blank environment variables file.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1631285984887/nFCPJNEH8.png)

The main variables to set values now are the URL and API key. At this point, you should consider the number of custom connectors you want to make as each collection you export will be a separate connector. To test the limits of the Custom Connector Editor, I moved each collection into a single new collection containing a folder for each collection:

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1631303921545/Mc0zQCCRE.png)

and then saved it as a V2.1 collection:

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1631304014977/CDIcYkHca.png)

Then trying to import this collection into Power Automate gave me this ever-helpful error message, 'Unable to convert array of different types into schema.'

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1631304203253/c-AsJdJO0.png)

### They can't all be winners

Using this method of starting with Postman collections and then trying to import to Power Automate custom connectors was a failure (for this API). I've since converted the collection to Swagger and imported the 514 actions, but with more than a hundred of them with errors, I don't think it will be possible to get through them all for a while. I'm going to ask on the next Project Coordinators call if anyone knows which actions have been requested and hope to submit a connector with just those actions in the coming weeks.
