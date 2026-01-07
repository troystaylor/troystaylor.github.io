---
title: "Power Platform IndiePubs: Starting again with Xero connectors"
author: Troy Taylor
date: 2021-09-07
category: Power Platform
layout: post
---

My three Independent Publisher Xero connectors were [submitted in June](https://github.com/microsoft/PowerPlatformConnectors/pull/891), but for various reasons, they haven't been certified yet. And that's okay with me, now that two weeks ago I found Xero's OpenAPI files. As my connectors haven't been certified, now is the time for me to start fresh and create new custom connectors for them before certification of the submitted connectors would lead to breaking changes. 

### Let's start the converting party!

Since the API files I've found are OpenAPI 3.0 files, they will need to be converted to Swagger 2.0 files before using them in the Power Automate editor. I can't recommend [APIMatic Transformer](https://www.apimatic.io/transformer) enough, but it is quite pricy if you are only going to use it for converting APIs. For a similar free tool, try LucyBot's [API Spec Converter](https://github.com/LucyBot-Inc/api-spec-converter):

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1630701913176/aOZ_3HEss.png)

This tool also allows you to convert between OpenAPI 3.0 and Swagger, amongst others. If you find the loading spinner taking too long, you may need to try using the command-line tool.

### Back to the custom connector editor

At this point, I find I like to check my work, so rather than continuing to modify and edit the now-converted Swagger file in Visual Studio Code, I switch back to the custom connector editor in Power Automate. You're going to have to test the connector(s) before submitting them anyway, so this helps start that process. I create a new blank connector, name it correctly and provide a description for the service, add an icon just for testing as it won't be submitted in the pull request, and set the background color to the dominant logo color. Switch over to the Swagger Editor and you'll see all of the other service fields that are now empty.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1630777408125/BF3kwm_QH.png)

You can now copy from the Swagger API file all of those missing fields. For larger APIs, it isn't uncommon to see 20-40 errors. It will take a few moments for the now complete file to be debugged by the editor and then, here be errors.                                                      

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1630783356950/ff_-lKtSU.png)
 
You are going to need to fix all of these errors before being able to save it, so if you need to take a break, copy the entire editor YAML code to a local file. For Xero Accounting, there are only two types of errors - "Equivalent paths are not allowed" and "Operations with parameters of "type: file" must include "multipart/form-data" in their "consumes" property." The previous error relates to path endpoints that have the same base path that would cause those actions to run improperly if they run at all without erroring. An example of this is these two actions with different end path parameters.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1630784756255/CAw1LXLRs.png)

Depending on how the actions need to run, you may be able to combine them in the same endpoint or you may need to choose which action is available in the connector. For this Xero connector, they can be combined by renaming the AttachmentID parameter to AttachmentIDOrFileName, as in either case, that parameter is just a string. Update the action and parameter descriptions then delete the erroring action. For the second error type, you will need to loop through the code finding these parameters of the file type.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1630784011743/n386M-cRe.png)

You can then add the additional multipart/form-data type to the consumes property.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1630784128322/nxy-O0TPh.png)

### The errors are gone, for now...

Once you get your custom connector(s) saved, you are welcome to test them and use them in Power Automates - we're not going to make any more changes within your environment. As I've mentioned before, now is the time to download them using the Power Platform CLI and work on fixing the validation errors within your favorite code editor. As this code for Xero Account is now over 20,000 lines long, there are many more hours of work to do before this connector can be submitted and there are 8 more APIs for Xero to work on.

***After I finished this post and started on the cleanup work, I found that one of the response references, /batchpayment, contained references to multiple other references. This isn't uncommon and reduces the amount of code that is duplicated, but the number of object schemas is so high (above 512), the editor cannot save the file. I have filed a [bug](https://github.com/microsoft/PowerPlatformConnectors/issues/1088) as I can't find this limitation in either the Swagger or JSON documentation.***
