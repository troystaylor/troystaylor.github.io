---
title: "Power Platform IndiePubs: How to make my certified Etsy connector better"
author: Troy Taylor
date: 2021-09-03
category: Power Platform
layout: post
---

If you've had a chance to check out the Independent Publisher connectors repo on [GitHub](https://github.com/troystaylor/PowerPlatformConnectors/tree/dev/independent-publisher-connectors), you may have noticed the Etsy connector I built was certified two weeks ago. This was the first connector I built after the Independent Publisher program was announced and as someone who is always learning, I knew I was submitting it to the best of my abilities, but perhaps not perfect. While feedback has not yet reached me, I heard from Natalie Pienkowska (https://twitter.com/nataliepienkow1) that Microsoft is receiving comments that the connector doesn't have response schemas. To which I will acknowledge that I did not build them.

If you've ever looked at building a custom connector for the Power Platform using the editor, you will know that you need to populate the General section and use the 'Import from Sample' button to generate the request parameters. 

![brave_Bv6CwG4o2P.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1630024303790/m-sXkTsVt.png)

You can save the connector and go use it right away. This is a happy way I build connectors "by hand" but the problem is that you have to then have to test the action once and then copy the response into a Parse JSON action. For more dynamic APIs that allow you to add custom fields, it may be easier to change the Parse JSON schema than to change the entire connector.

So let's go back to my Etsy connector. Yes, I will admit the currently certified connector has a less-than-optimal user experience. And looking at that screenshot above, the custom connector UI allows you to define the response. If you look at the default response:

![brave_5bmJIN5WFL.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1630024683010/jAF6ecd4Q.png)

the body is populated with key-body-output. That's not very helpful. What is better is a schema that looks like this, which is what you will get after supplying the editor with a sample response:

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1630024870475/1fK08tOmV.png)

While the properties are still improperly lowercase, this can be fixed by giving each an x-ms-summary (and you should enter a complete description as well). I would highly recommend that you don't do this within the editor - download the connector using the Power Platform Connectors CLI and go to work in your favorite code editor.

If you would like to follow the certification process, I have now submitted a [v1.1 pull request](https://github.com/microsoft/PowerPlatformConnectors/pull/1074) with responses defined and it should be available in the Power Platform in the next few weeks.
