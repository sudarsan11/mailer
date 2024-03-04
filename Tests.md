1) Authentication
    a) Happy path for initializing from cli
    b) Happy path for initializing from file
    c) Pass invalid credentials, expired credentials
    d) Pass empty file, invalid file path

2) Ingestion service
    Email fetcher
        a) Happy path for ingestion message for a user
        b) Initialize with invalid date range, non existing email id
        c) Fetch labels with invalid user id
        d) Fetch messages with invalid filters which are not supported by gmail api
        e) Fetch message with batch size greater than supported by gmail api
    Email processor
        a) Happy path for processesing message
        b) Pass duplicate senders to create senders
        c) Pass duplicate labels to create labels
        d) Duplicate message, header, value combination to message headers
        e) Create message for non existing senders

3) Rules service
    a) Happy path for rules service
    b) Pass empty file, invalid file path
    c) Pass conditions with invalid field, predicate, value combinations

4) Search service
    a) Happy path for search service with different rule combinations
    b) Pass conditions which match no messages in db
    c) Pass conditinos for invalid headers
    d) Pass conditinos for invalid header value

5) Action service
    a) Happy path for action service with different actions
    b) Pass invalid actions
    c) Pass invalid label to add / remove