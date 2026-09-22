# Releasing

Pushing a tag `v<version>` runs the [release workflow](.github/workflows/release.yml). It runs
all CI tests, then publishes one artifact per Chisel group to Maven Central with
[sbt-ci-release](https://github.com/sbt/sbt-ci-release). The version is the tag without the
`v`.

```bash
git tag v0.1.0
git push origin v0.1.0
```

The artifacts usually show up on Maven Central within an hour. Versions follow early
semver: before 1.0.0, a minor version bump (0.1 to 0.2) may break compatibility.

## One-time setup

1. Sign in at [central.sonatype.com](https://central.sonatype.com) with the `tjarker` GitHub
   account and check under Namespaces that `io.github.tjarker` is verified.
2. Generate a user token (account menu, "View Account", "Generate User Token").
3. Create a GPG signing key and publish its public part:

   ```bash
   gpg --gen-key
   gpg --list-keys                  # the long hex string is the key id
   gpg --keyserver keyserver.ubuntu.com --send-keys <key id>
   gpg --armor --export-secret-keys <key id> | base64 | tr -d '\n'   # PGP_SECRET
   ```

4. Add these repository secrets on GitHub (Settings, "Secrets and variables", "Actions"):

   | Secret | Value |
   |---|---|
   | `SONATYPE_USERNAME` | user token name |
   | `SONATYPE_PASSWORD` | user token password |
   | `PGP_SECRET` | output of the last command in step 3 |
   | `PGP_PASSPHRASE` | passphrase of the GPG key |
