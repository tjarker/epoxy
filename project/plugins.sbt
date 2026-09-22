// Publishes to Maven Central from GitHub Actions and derives the version from git tags.
addSbtPlugin("com.github.sbt" % "sbt-ci-release" % "1.12.1")

// Fetches firtool binaries from Maven Central; the Chisel 5 build uses it (see build.sbt).
libraryDependencies += "org.chipsalliance" %% "firtool-resolver" % "2.1.1"
