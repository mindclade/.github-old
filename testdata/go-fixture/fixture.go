// Package fixture exists so reusable-go-ci has something real to build, vet, lint and test.
package fixture

// Add returns a + b. The function is trivial on purpose: the smoke test proves the workflow
// runs, not that arithmetic works.
func Add(a, b int) int {
	return a + b
}
