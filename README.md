[![codecov](https://codecov.io/gh/barrelmaker97/concourse-hangouts-resource/branch/master/graph/badge.svg?token=4CX85DLIC0)](https://codecov.io/gh/barrelmaker97/concourse-hangouts-resource)
[![CodeFactor](https://www.codefactor.io/repository/github/barrelmaker97/concourse-hangouts-resource/badge/master)](https://www.codefactor.io/repository/github/barrelmaker97/concourse-hangouts-resource/overview/master)

# Concourse Google Hangouts Resource
A [Concourse](http://concourse.ci/) resource to post a message to Google Hangouts room using webhooks. The message includes the pipeline name, job name and build number which the resource is running under, and an optional message/message file.

## Resource Type Configuration

```yaml
resource_types:
  - name: hangouts-resource
    type: docker-image
    source:
      repository: ghcr.io/barrelmaker97/concourse-hangouts-resource
      tag: latest
```

## Resource Configuration

* `webhook_url`: _Required - (String)_. The webhook generated for Hangouts channel. (i.e. https://chat.googleapis.com/v1/spaces/ABC/messages?key=DEF)

### Example

```yaml
resources:
- name: hangouts
  type: hangouts-resource
  source:
    webhook_url: ((webhook_url))
```

## Behavior

### `check`: Non-functional

### `in`: Non-functional

### `out`: Post message to Hangouts chat room

Posts the given message to a Google Hangouts Room that corresponds to the provided webhook. It includes information from the current running build such as the pipeline name, job name, and build number as defined in the pipeline.

#### Parameters

* `message`: _Optional - (String)_. The message to post along the other information to Hangouts room.
* `message_file` _Optional - (String)_. Path to file containing text to append to `message`)
* `post_url` _Optional - (Boolean)_. Include link to the current job. (*Default:* `true`)
* `post_info` _Optional - (Boolean)_. Include info about the current job. (*Default:* `true`)
* `create_thread` _Optional - (Boolean)_. Create a new thread in the chat room for each message. (*Default:* `false`)

### Example

It's recommended to use this resource in the `try:` step so that your build doesn't fail if the resource fails to send the message.

```yaml
jobs:
  - name: some-job
    plan:
      - try:
          put: hangouts
          params:
            message: "Building version: "
            message_file: project/version.txt
            post_url: true
            create_thread: false

      # .
      # .
      # .
      # Some steps to execute
      # .
      # .
      # .

    on_failure:
      try:
        put: hangouts
        params:
          message: Job Failed!
          post_url: false
          create_thread: false

    on_success:
      try:
        put: hangouts
        params:
          message: Job Succeeded!
          post_url: false
          create_thread: false
```

## Complete Example:
This is a working example of a pipeline file that does absolutely nothing other then posting to Hangouts.

You can test it as is after passing `webhook_url` while setting up the pipeline or replacing `((webhook_url))` in place with the webhook URL.
```yaml
---
resource_types:
  - name: hangouts-resource
    type: docker-image
    source:
      repository: ghcr.io/barrelmaker97/concourse-hangouts-resource
      tag: latest
resources:
  - name: hangouts
    type: hangouts-resource
    icon: google-hangouts
    source:
      webhook_url: ((webhook_url))
jobs:
  - name: test-job
    plan:
      - put: hangouts
        params:
          message: Greetings from Concourse!
          post_url: true
          create_thread: false
```

## License

BSD 2-Clause
