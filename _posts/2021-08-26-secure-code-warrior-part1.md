---
title: "Power Platform IndiePubs: Adventures in Code Training with Secure Code Warrior, Part 1"
author: Troy Taylor
date: 2021-08-26
category: Power Platform
layout: post
---

Last month, I was assigned to a client project to help them transform manual reporting of trainings and tournaments from the Secure Code Warrior platform to Microsoft Dataverse. This is a very common scenario with Power Platform - take a complex, challenging-to-maintain data source that is being managed in a series of Excel files and transform it into a low-code app for end-users. My assignment was because I checked a number of boxes: can build canvas and model-driven Power Apps, can build a custom connector to the SCW API, and can work in very tight sprints.

If you take a look at the current SCW API ([v2](https://portal-api.securecodewarrior.com/api/docs/v2/)), you will find a well-documented site containing authentication, operations, and schema definitions. The one thing you will not find is the OpenAPI spec file. Using the connection of my client, I was able to reach out to SCW and they shared a file with me. I'm not going to link to that file as you will see by the end of this post, Microsoft has already certified my Swagger-based Independent Publisher connector. But if you are starting to build a custom connector for an API that does have an OpenAPI file, please note you may need to convert it to Swagger first. Since the file provided to me was a Swagger YAML file, I started by creating a new blank connector, flipping the switch for the Swagger Editor, and pasting the YAML code into the editor.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1629935772136/BZk8nPfax.png)

After pasting:

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1629935975487/AB4ygogy5.png)

You may think you can save and go start using the connector, but have you ever heard that no two programmer write the same code? Behind every great API, there are probably several (if not many) people helping shape it behind the scenes. Trying to save the code now will error out with an error message:

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1629936227506/l2BYk06H0.png)

Switching back to the Definitions tab, you will find a number of warnings and errors on different actions. Most of these errors are due to missing operation IDs, so fixing those using the Definitions tab UI will save you time versus manually reviewing the Swagger.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1629936460080/VKeRLAthB.png)

Once I fixed all the errors and bugs that the Custom Connector UI found, I was able to save the connector. Before downloading the connector using the Power Platform Connector CLI, I did review that I was able to connect to SCW using an API key and tested several of the basic get actions. At this point with most connectors, whether I build the connector from a file or manually create all the actions needed from the API, I tend to consider myself about one-third of the way done. Validating the downloaded connector will inevitably find dozens if not hundreds of errors and warnings. Even using the Find/Replace actions in Visual Studio Code, this can take many hours to fix. There's also the matter of correcting or writing new parameter descriptions. You'll then need to create a README file documenting the actions and other API requirements. But after spending all that time preparing the connector, you'll submit it to the [Power Platform Connectors repo](https://github.com/microsoft/PowerPlatformConnectors), and wait a couple of weeks until you here that the connector was certified. And as of yesterday, after doing all these steps above, I got the GitHub notification that my pull request was merged into Dev (thanks [Srikanth](https://github.com/sriyen-msft)!).

You can now find my Independent Publisher connector on the Power Platform, with [documentation here](https://docs.microsoft.com/en-us/connectors/securecodewarrior/) and [the certified repo here](https://github.com/microsoft/PowerPlatformConnectors/tree/dev/independent-publisher-connectors/Secure%20Code%20Warrior). 

This is the first post in a series about Secure Code Warrior and integrating their data into the Power Platform.
