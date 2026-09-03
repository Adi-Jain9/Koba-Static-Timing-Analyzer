module circuit (
	input wire a,
	input wire b,
	input wire c,
	input wire clk,

	output wire d,
	output wire e,
	output wire f
);
	
	wire q1;

	wire n1;
	wire n2;
	wire n3;
	wire n4;
	wire n5;
	wire n6;
	wire n7;
	wire n8;
	wire n9;
	wire n10;


	DFF_X1 FF1 (
		.CLK(clk),
		.D(a),
		.Q(q1)
	);

	INV_X1 INV1 (
		.A(q1),
		.Y(n1)
	);

	INV_X1 INV2 (
		.A(n1),
		.Y(n2)
	);

	INV_X1 INV3 (
		.A(n1),
		.Y(n3)
	);
	
	NAND3_X1 NAND1 (
		.A(n3),
		.B(b),
		.C(c),
		.Y(n4)
	);

	INV_X1 INV4 (
		.A(n4),
		.Y(n5)
	);

	NAND2_X1 NAND2 (
		.A(n2),
		.B(n5),
		.Y(d)
	);

	INV_X1 INV5 (
		.A(n4),
		.Y(n6)
	);

	INV_X1 INV6 (
		.A(c),
		.Y(n7)
	);

	NAND2_X1 NAND3 (
		.A(n4),
		.B(n7),
		.Y(n8)
	);

	INV_X1 INV7 (
		.A(n8),
		.Y(n9)
	);

	NAND2_X1 NAND4 (
		.A(n6),
		.B(n8),
		.Y(e)
	);

	DFF_X1 FF2 (
		.CLK(clk),
		.D(n9),
		.Q(f)
	);

endmodule
