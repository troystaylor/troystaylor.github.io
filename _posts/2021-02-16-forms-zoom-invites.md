---
title: "Power Platform IndiePubs: Using Microsoft Forms to send Zoom invites"
author: Troy Taylor
date: 2021-02-16
category: Power Platform
layout: post
---

After building and submitting connectors for Zoom and Badgr, I wanted to start using both in flows or apps as that is part of the test process. The Zoom connector only has actions, so the only real way to test it is to build a flow or import their collection into Postman. Here's the scenario I chose:

I want users to fill in a Microsoft Form and then automatically receive a personalized Zoom invitation in their inbox.

I created a new form for Zoom meeting invites with two fields: Email and Name. I then created a new flow in Power Automate with a trigger: **When a new response is submitted** (Microsoft Forms).

After that action, I added a **Get response details** (Microsoft Forms) and used the Response Id from the trigger and the Form Id.

Now that I have the users' email and name, I need to create the meeting. Using the **Create a meeting** (Zoom) action, I'll provide a topic, start time, and duration in minutes. From the list of outputs, I'll need the **Join URL** and **Start Time**.

The next step is converting the string of numbers in **Start Time** to a useable date and time for our meeting invite. I used a compose action to use the function:

`convertFromUtc(outputs('Create_a_meeting')?['body/start_time'],'Eastern Standard Time')`

Essentially using the output from **Create a meeting** to pass into the function and then converting the UTC into our desired time zone string. You can see a list of valid time zone strings [here](https://docs.microsoft.com/en-us/previous-versions/windows/embedded/gg154758(v=winembedded.80)?redirectedfrom=MSDN).

The result is another string with a `T` separating date and time, so a second compose action uses this function:

`replace(outputs('Compose'),concat('T',' '))`

This swaps out the `T` with a space so the string is 'readable'.

The final action before sending the email is creating the calendar invite as a .ics file. Using the **Create event (V4)** (Office 365 Outlook) action, I added the **Responder's Email** as the required attendees, the Form Id as the subject to be very clear, the **Join URL** and the formatted date and time for the body of the email. For the start and end time, I used the outputs from **Create a meeting** for **Start Time** and **Start Time**. I then provided a time zone string and selected yes for the **Is HTML** field.

In another compose action, I add this function:

`base64(outputs('Create_event_(V4)')?['body/icalUId'])`

This converts the output from **Create event (V4)** into a base64 string. And now for the last action, add a **Send an email (V2)** (Office 365 Outlook) action with:

- To: **Responder's Email**
- Subject: Same subject as the calendar event (**Form Id**)
- Body: Any HTML you'd like for the body of the message, including the outputs from **Create a meeting** for **Join URL** and the formatted date and time
- Attachments name-1: invite.ics
- Attachments Content-1: Output from the final Compose action

You can now test the flow by submitting a response on the form and waiting for the email. Let me know if you run into any problems or would like to suggest improvements by tweeting me [@troystaylor](http://twitter.com/troystaylor).
