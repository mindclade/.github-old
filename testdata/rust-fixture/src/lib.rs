//! Exists so reusable-rust-ci has something real to fmt, clippy and test.

/// Adds two numbers. Trivial on purpose — the smoke test proves the workflow runs.
pub fn add(a: i64, b: i64) -> i64 {
    a + b
}

#[cfg(test)]
mod tests {
    use super::add;

    #[test]
    fn adds() {
        assert_eq!(add(2, 3), 5);
    }
}
