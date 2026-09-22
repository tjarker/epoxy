import sbt._

/** Chisel releases that are binary compatible with each other.
  *
  * epoxy is built and published once per group. Each build is compiled against the oldest
  * release of its group, so the published artifact works with every release of the group.
  *
  * @param projectId    sbt project id, also used in the artifact name
  * @param organization Maven group of the Chisel artifacts
  * @param library      Chisel artifact name; its compiler plugin is `<library>-plugin`
  * @param version      oldest release of the group
  * @param scalaVersion newest Scala version the compiler plugin of `version` was published for
  */
case class ChiselGroup(
  projectId: String,
  organization: String,
  library: String,
  version: String,
  scalaVersion: String,
) {

  /** Chisel 3 emits Verilog with its built-in compiler; Chisel 5 and later use firtool. */
  def isChisel3: Boolean = library == "chisel3"

  /** Suffix of the source folders holding code that differs between Chisel 3 and Chisel 5+. */
  def sourceSuffix: String = if (isChisel3) "chisel3" else "chisel5plus"

  def dependency: ModuleID = organization %% library % version

  def compilerPlugin: ModuleID =
    organization % s"$library-plugin" % version cross CrossVersion.full
}

object ChiselGroup {
  val chisel35 = ChiselGroup("chisel35", "edu.berkeley.cs", "chisel3", "3.5.6", "2.13.10")
  val chisel36 = ChiselGroup("chisel36", "edu.berkeley.cs", "chisel3", "3.6.1", "2.13.14")
  val chisel5 = ChiselGroup("chisel5", "org.chipsalliance", "chisel", "5.0.0", "2.13.10")
  val chisel6 = ChiselGroup("chisel6", "org.chipsalliance", "chisel", "6.0.0", "2.13.12")
  val chisel7 = ChiselGroup("chisel7", "org.chipsalliance", "chisel", "7.0.0", "2.13.16")
}
