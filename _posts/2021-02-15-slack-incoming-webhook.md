---
title: "Power Platform IndiePubs: Send a message to a Slack channel using Incoming Webhooks"
author: Troy Taylor
date: 2021-02-15
category: Power Platform
layout: post
---

In this blog post, I'm going to show you how to send messages to a Slack channel using Microsoft Power Automate in a couple of minutes. 

### Create a Slack Incoming Webhook

Login to your Slack workspace and click on your workspace name in the top left. Then select **Settings & Administration** and then **Manage Apps**. Alternatively, you can head straight to [https://WORKSPACE_URL.slack.com/apps/manage](https://WORKSPACE_URL.slack.com/apps/manage). This will take you to the main Slack App Directory in a new tab. Search for **Incoming Webhooks** and click on **Add to Slack**. 

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1613403613026/KQBvyeqRR.png)

Then select the **channel** you want to post to and click **Add Incoming Webhooks integration**.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1613403697669/lQ5Zdt_2z.png)

Copy your **Webhook URL** and store that somewhere safe. This is the only time you will be able to copy your webhook URL and you will need to enter it into Power Automate.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1613403777321/lA2cjOTNp.png)

### Create a new flow in Power Automate

Head over to [https://us.flow.microsoft.com/](https://us.flow.microsoft.com/) and create a new instant cloud flow. 

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1613403894374/RCuNdBTi3.png)

Give your flow a name, select **Manually trigger a flow**, and click **Create**.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1613403966999/mQmDx7XdR.png)

Click on **New Step** and search for HTTP, selecting the **HTTP** action. For the **Method** field, select **POST** and paste your Slack Webhook URL from above into **URI**. Under headers, you will add **Content-Type** and **application/json**. Under **Body** paste the following:

```
{
    "text":"Hello from Power Automate."
}
```

You should have something looking like this when you are done:

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1613404260562/iM7vCl8Wl.png)

Click **Save** and then **Test**, select **Manually**, and **Test** again. Now **Run flow** and **Done**. In a few moments, you should have a green checkmark that the flow ran successfully and if you check Slack, your message should have appeared in the channel you selected.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1613404464859/Nj52_Vm6k.png)
