#include <stdio.h>
#include <stdlib.h>

int n, count = 0;
int board[10];

// Check whether a queen can be placed at (row, col)
int isSafe(int row, int col) {
    for (int i = 0; i < row; i++) {
        if (board[i] == col || abs(board[i] - col) == row - i) {
            return 0;
        }
    }
    return 1;
}

// Place queens row by row using backtracking
void solve(int row) {
    if (row == n) {
        count++;
        return;
    }
    for (int col = 0; col < n; col++) {
        if (isSafe(row, col)) {
            board[row] = col;
            solve(row + 1);
        }
    }
}

int main() {
    scanf("%d", &n);
    solve(0);
    printf("%d\n", count);
    return 0;
}
