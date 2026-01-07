---
title: "Power Platform IndiePubs: Creating messages for Slack using Block Kit"
author: Troy Taylor
date: 2021-02-16
category: Power Platform
layout: post
---

After playing around with Slack webhooks over the last week, I'm beginning to understand the usefulness of Block Kit. While you can send a very simple message to a Slack channel using a webhook with a body like this:

```
{
    "text":"Hello from Power Automate."
}
```

you are limited in what you can do with that message. You can't add headers, multi-column layouts, buttons, or images. You can do all of that using [Block Kit](https://api.slack.com/block-kit).

Slack has a wonderful [Block Kit Builder](https://app.slack.com/block-kit-builder/) where you can use a template or start from scratch. 

For this post, I'm going to convert the Approval message template to work in Power Automate. The first thing you will notice is the payload field and the very long block of text. If you try to use this same code in a Compose action in Power Automate (replacing the variables with the ones you want to use), you will notice an error. You need to change a few of the quotation marks to make the JSON syntax valid.

### Example  
Change

```
"fields": [
				{
					"type": "mrkdwn",
					"text": "*Type:*\nPaid Time Off"
				},
```

to

```
"fields": [
				{
					""type"": ""mrkdwn"",
					""text"": ""*Type:*\nPaid Time Off""
				},
```

In this example, I've added an additional quotation mark before `type`, `mrkdwn`, `text` and also added several quotation marks before the backslash characters at the end of both lines. Then save and check your syntax is correct. 

After you have updated the entire block of text, copy the entire contents from the Compose action and paste them into the Body for the HTTP action.

The result in Slack:

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1613492732267/mPO4nKJsP.png)
