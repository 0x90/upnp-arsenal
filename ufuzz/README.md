![UFuzz](http://pulpphikshun.files.wordpress.com/2014/04/ufuzzlogo.png?w=300&h=150)
==

UFuzz, or Universal Plug and Fuzz, is an automatic UPnP fuzzing tool. It will enumerate all UPnP endpoints on the network, find the available services and fuzz them. It also has the capability to fuzz HTTP using Burp proxy logs.

It is designed to fuzz embedded systems, and as such, is only single threaded. It also has a very limited payload set since fuzzing these systems can be slow. Certain payloads such as blind SQLi and command injection rely on delays to indicate whether the injection was successful, and may have false positives. Other payloads such as format strings and buffer overflows are designed to use a custom monitor to detect crashes.

Example configuration modules and monitor modules are included. Custom monitors allow the use of target system telemetry to detect crashes. Example modules have been provide for telnet-based and serial console based crash detection.

Note that the code is very rough around the edges. "Hacky" would be the best way to describe it. Unfortunately this project was written quickly and really never properly architected. I will be working to resolve this in the coming months.

Finally, some of the code was borrowed from other projects:

* The UPnP code is based largely on Craig Heffner's miranda code. Craig has been an inspiration to me and I highly recommend you read his blog [/dev/ttys0](http://www.devttys0.com).

* Some of the test set generation code is based on Ben Nagy's Metafuzz project.

* The socket and http parsing code is based on [Excon](https://github.com/geemus/excon).

Installation
----

UFuzz has been tested with Ruby 1.9.3 and Ruby 2.1.1. You can install all the required gems by running `bundle install` in the UFuzz directory.

Usage
----

Run ufuzz with the -h option to see all command line options. When the tool runs, logs are written into the log directory.

For basic fuzzing of all UPnP devices on the network, just run `ufuzz --upnp`.  You will probably also want to use the `-v 4` option to see the requests and response summaries.