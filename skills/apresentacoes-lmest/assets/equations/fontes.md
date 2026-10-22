# Fontes LaTeX das referências de equação

Estas são as expressões usadas para gerar `eq_1.png`, `eq_2.png` e `eq_3.png`
com `scripts/render_equations.py` (20 pt, Latin Modern, 300 dpi). Elas mostram
as convenções do LMEst: vetores e matrizes em negrito vertical (`\mathbf`),
pontos de derivada com `\dot`/`\ddot`, matrizes com colchetes altos
(`bmatrix`) e equações empilhadas centralizadas (`gather`).

## eq_1 — relações algébricas (força e corrente)

$$
\begin{gathered}
F = k_s x + k_i i \\
i = \mathbf{C_c x_c} - \mathbf{D_c} x
\end{gathered}
$$

## eq_2 — dinâmica estrutural e transformação modal

$$
\begin{gathered}
\mathbf{M\ddot{x}} + \mathbf{C\dot{x}} + \mathbf{Kx} = \mathbf{F} \\
\mathbf{x} = \mathbf{\Phi q} \\
\mathbf{M_m\ddot{q}} + \mathbf{C_m\dot{q}} + \mathbf{K_m q} = \mathbf{\Phi}^T\mathbf{F}
\end{gathered}
$$

## eq_3 — matrizes e vetores

$$
\begin{gathered}
\phi^T = \begin{bmatrix}
1 & \cdot & \cdot & \cdot & \cdot & \cdot & \cdot & \cdot & \cdot \\
\cdot & 1 & \cdot & \cdot & \cdot & \cdot & \cdot & \cdot & \cdot \\
\cdot & \cdot & \cdot & \cdot & \cdot & 1 & \cdot & \cdot & \cdot \\
\cdot & \cdot & \cdot & \cdot & \cdot & \cdot & 1 & \cdot & \cdot
\end{bmatrix}
\qquad
\phi^T\mathbf{x} = \begin{bmatrix} x_1 \\ y_1 \\ x_2 \\ y_2 \end{bmatrix} \\[6pt]
\mathbf{R} = \begin{bmatrix}
\cos\theta & \sin\theta & 0 & 0 \\
-\sin\theta & \cos\theta & 0 & 0 \\
0 & 0 & \cos\theta & \sin\theta \\
0 & 0 & -\sin\theta & \cos\theta
\end{bmatrix}
\qquad
\begin{bmatrix} v_1 \\ w_1 \\ v_2 \\ w_2 \end{bmatrix} = \mathbf{R}
\begin{bmatrix} x_1 \\ y_1 \\ x_2 \\ y_2 \end{bmatrix}
\end{gathered}
$$
