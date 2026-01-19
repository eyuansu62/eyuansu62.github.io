#!/bin/bash

# Add Homebrew Ruby to PATH
export PATH="/opt/homebrew/opt/ruby/bin:$PATH"

# Set SDKROOT for any native extensions that might need to be built
export SDKROOT=$(xcrun --show-sdk-path)

# Install dependencies if needed
bundle check || bundle install

# Start the server
echo "Starting local server..."
echo "Open http://127.0.0.1:4000 in your browser"
bundle exec jekyll serve
