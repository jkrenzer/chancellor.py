# Local .ssh setup files

In this directory certain files intended for `.ssh` can be put and are transferred (on every
container start or by manual command execution) to the container's SSH user directory.

## Files

- `authorized_keys`: Authorized public SSH keys to connect to the container
  - One key per line, as obtained from your local `.ssh/id_*.pub` file
  - Run `ssh-update-keys` to update if you have added or removed a key
