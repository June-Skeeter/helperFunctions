# Helper Functions

A collection of helpful tools for data processing, best used as a submodule in other applications.

## Adding a submodule

Command line syntax for adding a submodule:

`git submodule add repository-url path/to/submodule`

* path/to/submodule is a relative to the base of the "parent" module.  submodules/helperFunctions would be a good choice.


## Updating a submodule

To update a local copy repo and its submodules from remote

`git pull --recurse-submodules`

To make, commit, and push changes to a submodule made from within a parent repo

`cd path/to/submodule`
`git checkout -b submodUpdates`

Make whatever changes then commit.  It is important to create a new branch, because submodules heads are often detached from the main branch.

`git commit -am "some changes to a submodule"`

Merge back to main then delete the updates branch

`git checkout main`
`git merge submodUpdates`
`git branch -D submodUpdates`

Navigate back to the base of the "parent" module.  Commit changes to the submodule (plus any changes within the module its self), then push to remote.

`cd ../../..`
`git commit -am "updated submodule"`
`git push --recurse-submodules=on-demand`

