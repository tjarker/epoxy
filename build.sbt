// epoxy is built once per Chisel compatibility group (see project/ChiselGroup.scala).
// Every group compiles the same sources from src/; the root project only aggregates them.

ThisBuild / organization := "io.github.tjarker"
ThisBuild / version := "0.1.0-SNAPSHOT"
ThisBuild / scalacOptions ++= Seq("-deprecation", "-feature", "-unchecked")

def sourceDirs(root: File, scope: String, group: ChiselGroup): Seq[File] =
  Seq(root / "src" / scope / "scala", root / "src" / scope / s"scala-${group.sourceSuffix}")

def groupProject(group: ChiselGroup): Project =
  Project(group.projectId, file("builds") / group.projectId)
    .settings(
      name := s"epoxy-${group.projectId}",
      scalaVersion := group.scalaVersion,
      libraryDependencies ++= Seq(
        group.dependency,
        "org.scalatest" %% "scalatest" % "3.2.19" % Test,
      ),
      addCompilerPlugin(group.compilerPlugin),
      Compile / unmanagedSourceDirectories := sourceDirs((ThisBuild / baseDirectory).value, "main", group),
      Test / unmanagedSourceDirectories := sourceDirs((ThisBuild / baseDirectory).value, "test", group),
      Test / fork := true,
      Test / run / fork := true,
    )

lazy val chisel35 = groupProject(ChiselGroup.chisel35)
lazy val chisel36 = groupProject(ChiselGroup.chisel36)

// Chisel 5 needs firtool on PATH to emit Verilog. The firtool versions it was released with
// (1.40 to 1.43) are not on Maven Central, so its tests use the oldest one that is. Newer
// versions no longer accept the options Chisel 5 passes.
lazy val chisel5 = groupProject(ChiselGroup.chisel5)
  .settings(
    Test / envVars := {
      val firtool = firtoolresolver.Resolve("1.51.0", false) match {
        case Right(binary) => binary.path
        case Left(error) => sys.error(s"could not fetch firtool: $error")
      }
      Map("PATH" -> s"${firtool.getParent}${java.io.File.pathSeparator}${sys.env("PATH")}")
    },
  )

lazy val chisel6 = groupProject(ChiselGroup.chisel6)
lazy val chisel7 = groupProject(ChiselGroup.chisel7)

lazy val root = (project in file("."))
  .aggregate(chisel35, chisel36, chisel5, chisel6, chisel7)
  .settings(
    name := "epoxy",
    scalaVersion := ChiselGroup.chisel7.scalaVersion,
    Compile / unmanagedSourceDirectories := Nil,
    Test / unmanagedSourceDirectories := Nil,
    publish / skip := true,
  )
