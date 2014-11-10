---
layout: post
title: "Streaming in VTK : Time"
---

With this blog, I am starting another series. This time we will cover streaming
in VTK. In this context, we define streaming as the process of sequentially
executing a pipeline over a collection of subsets of data. Example of streaming
include streaming over time, over logical extents, over partitions and over
ensemble members. In this article, I will cover streaming over time. In future
ones, we will dig into other types of streaming. I am assuming that you understand
the basics of how the VTK pipeline works including pipeline passes and using
keys to provide meta-data and make requests. If you are not familiar with these
concepts, I recommend checking out my previous blogs, specially
[[1]({% post_url 2014-09-18-pipeline %})], [[2]({% post_url 2014-10-05-pipeline-2 %})]
and [[3]({% post_url 2014-10-26-pipeline-3 %})].

## Problem statement

Let's look at a flow-field defined over a 2D uniform rectilinear grid. We will
pick a viscous flow that has a known closed-form solution so that we don't have to
write a solver. I chose a problem from my favorite graduate level fluid mechanics book:
Panton's "Incompressible Flow". From section 11.2, flow over Stoke's oscillating
plate is a great example. Without getting into a lot of details, the solution for
this problem is as follows.

![Stoke's plate](/assets/flow-over-plate.png)

This is a nice flow-field to study because it is very simple but is still time variant. This
profile looks as follows (click to animate):

<figure>
<img src="/assets/profile0.png" alt="Animation" style="margin-left:auto; margin-right:auto" onclick='javascript:this.src="/assets/profile.gif"'/>
</figure>
