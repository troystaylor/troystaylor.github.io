---
title: "Power Platform IndiePubs: Using Flic buttons to trigger a Power Automate Flow"
author: Troy Taylor
date: 2021-02-22
category: Power Platform
layout: post
---

*This post is copied from [my original post on Hashnode](https://troystaylor.hashnode.dev/power-platform-indiepubs-using-flic-buttons-to-trigger-a-power-automate-flow).*

As a side project over the weekend, I decided to connect my Flic buttons to Microsoft Power Automate. The Flic buttons I have are Flic 2, single-button Bluetooth devices that connect to a hub or directly to your phone. I've owned them for a few years now, but never used them to their full potential. Mostly because I didn't want to develop an Android app to use them. But checking through my phone yesterday, I noticed I had updates to the Flic app and looked at the integrations they now have. While there are several different triggers available and while some of them (like triggering a [Google Assistant routine](https://support.google.com/assistant/answer/7394306?co=GENIE.Platform%3DAndroid&hl=en)) is going to solve more complex tasks, I found the HTTP Request trigger.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1614013467988/qPHJ3Uq6V.png)

In this blog post, I'll show you how to connect a Flic button to Power Automate and test multiple button actions against a flow.

### Setup 

To set up the HTTP Request integration on your Flic button:

1. Open your Flic app
2. Click on the Plus symbol to add another integration
3. Select **Advanced** and then **HTTP Request**
4. Enter the URL from Power Automate (I have not entered it yet)
5. Select the **Request method** as **Post**
6. Leave **Content type** as **JSON**
7. In the **Request Body** field enter {}
8. Click **Add an action**

You need to create an instant trigger flow in Power Automate and then use the returned URL as the URL for your Flic button. 

1. Create a new Instant cloud flow in Power Automate with an HTTP Request trigger
2. Save the flow and wait for the URL to populate
3. Copy the URL and paste it into the Flic HTTP Request
4. Click Save in the Flic App

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1614014343056/lQdGgfWPM.png)

### Test your first flow

Back in the Flic app, you can click on the little **Play** icon next to the URL field and Power Automate will pick up the request and run your flow. You can decide what you want this button action to do, for example sending yourself a mobile notification.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1614014669935/uJBkS7QPk.png)

Save the flow and test your Flic button. I had a green check mark on the trigger in a few seconds and then my mobile notification in another few seconds.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1614015026773/tZpQVV_e7.png)

### Multiple clicks

So far you have a working physical button that can call a Power Automate flow with a single click. Using a little bit of boolean, you can expand the flow to work with a double-click and hold of the Flic button. Now in the Flic app you'll also want to add two more HTTP Request actions for those other button clicks. The URL will remain the same for all three clicks, but now we want to update the Request Body to show the action type. 

`{"action": "click"}`

`{"action": "double-click"}`

`{"action": "hold"}`

Now in Power Automate, we are going to add a Parse JSON action and pass the Body from the HTTP request trigger into it. Click on Generate from sample and then paste in any of the three examples from above. You'll have this schema when complete.

```
{
    "type": "object",
    "properties": {
        "action": {
            "type": "string"
        }
    }
}
```

After the Parse JSON action, add a Switch action that will use the value from action. Then under each case, you can decide what actions to perform. In my test flow, I chose to send different notification messages for the different button actions.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1614015832663/OXnQSrxhF.png)

And that's it!
